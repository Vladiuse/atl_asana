import logging
from collections.abc import Generator
from dataclasses import asdict, dataclass
from time import sleep
from typing import TYPE_CHECKING, Any

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from asana.models import AtlasUser
from asana.services import AsanaCommentPrettifier, get_user_profile_url_mention_map
from common.utils import normalize_multiline
from django.db import transaction
from django.db.models import Q, QuerySet
from message_sender.client import AtlasMessageSender

from .collectors.comment_data import CommentDataCollector
from .collectors.dto import CommentDto
from .collectors.exceptions import CommentDeletedError
from .models import (
    AsanaComment,
    AsanaWebhookProject,
    AsanaWebhookRequestData,
    ProjectIgnoredSection,
    ProjectNotifySender,
)
from .senders import BaseCommentSender
from .senders.registry import SENDERS_REGISTRY

if TYPE_CHECKING:
    from .senders.dto import CommentSendMessageResult


class ProcessAsanaNewCommentEvent:
    @dataclass
    class AsanaNewCommentEvent:
        comment_id: int
        user_id: int
        task_id: int

    @dataclass
    class Result:
        created_comments_count: int
        comments: list["ProcessAsanaNewCommentEvent.AsanaNewCommentEvent"]

    def _event_to_comment_dto(self, events_data: dict[str, Any]) -> list[AsanaNewCommentEvent]:
        result = []
        for event in events_data["events"]:
            if event["resource"]["resource_subtype"] == "comment_added" and event["user"] is not None:
                event_dto = ProcessAsanaNewCommentEvent.AsanaNewCommentEvent(
                    comment_id=event["resource"]["gid"],
                    user_id=event["user"]["gid"],
                    task_id=event["parent"]["gid"],
                )
                result.append(event_dto)
        return result

    def process(self, asana_webhook: AsanaWebhookRequestData) -> Result:
        events_data = asana_webhook.payload
        asana_comments_dto = self._event_to_comment_dto(events_data=events_data)
        for comment_dto in asana_comments_dto:
            AsanaComment.objects.create(
                comment_id=comment_dto.comment_id,
                user_id=comment_dto.user_id,
                task_id=comment_dto.task_id,
                project=asana_webhook.project,
            )
        asana_webhook.is_target_event = bool(asana_comments_dto)
        asana_webhook.save()
        return ProcessAsanaNewCommentEvent.Result(
            created_comments_count=len(asana_comments_dto),
            comments=asana_comments_dto,
        )


class AsanaCommentNotifier:
    def __init__(
        self,
        asana_api_client: AsanaApiClient,
        message_sender: AtlasMessageSender,
        comment_notifier: BaseCommentSender,
    ):
        self.asana_api_client = asana_api_client
        self.message_sender = message_sender
        self.comment_notifier = comment_notifier

    def _notify_profiles_not_found(self, comment_dto: CommentDto) -> None:
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
            ⚠️ Not found asana user for profiles:

            Task url: {task_url}
            Profiles: {comment_dto.profile_url_not_found_in_db}
        """
        message = normalize_multiline(message)
        self.message_sender.send_log_message(message=message)

    def process(self, comment_model: AsanaComment) -> None:
        """Process asana comment.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        comment_data_collector = CommentDataCollector(
            asana_api_client=self.asana_api_client,
        )
        try:
            comment_dto = comment_data_collector.collect(comment_model=comment_model)
        except CommentDeletedError:
            comment_model.mark_as_deleted()
            return
        if len(comment_dto.profile_url_not_found_in_db) > 0:
            self._notify_profiles_not_found(comment_dto=comment_dto)
        send_result: CommentSendMessageResult = self.comment_notifier.notify(comment_dto=comment_dto)
        comment_model.has_mention = comment_dto.has_mention
        comment_model.is_notified = send_result.is_send
        comment_model.send_result = asdict(send_result)
        comment_model.task_url = comment_dto.task_data["permalink_url"]
        comment_model.text = comment_dto.pretty_comment_text
        comment_model.save()


class ProjectCommentsGenerator:
    """Search comments in tasks and return it.

    In projects cant be ignored sections.
    """

    SLEEP_AFTER_FETCH_TASK = 0.2

    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def _get_project_active_sections(self, project: AsanaWebhookProject) -> list[dict[str, Any]]:
        """Get project active sections.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        ignored_sections_ids = [ignored_section.section_id for ignored_section in project.ignored_sections.all()]
        sections = self.asana_api_client.get_project_sections(project_id=project.project_id)
        return [section_data for section_data in sections if section_data["gid"] not in ignored_sections_ids]

    def generate(self, project: AsanaWebhookProject) -> Generator[dict[str, Any], None, None]:
        """Return comments from project sections.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        logging.info("%s: project: %s", self.__class__.__name__, project)
        sections_to_check = self._get_project_active_sections(project=project)
        logging.info("Sections to collect comments: %s", sections_to_check)
        for section_data in sections_to_check:
            section_tasks = self.asana_api_client.get_section_tasks(
                section_id=section_data["gid"],
            )
            logging.info("section: %s, tasks: %s", section_data["name"], len(section_tasks))
            for task_data in section_tasks:
                task_id = task_data["gid"]
                logging.info("Task: %s %s", task_id, task_data["name"])
                sleep(self.SLEEP_AFTER_FETCH_TASK)
                task_comments = self.asana_api_client.get_comments_from_task(
                    task_id=task_id,
                    opt_fields=["gid", "created_by", "resource_subtype"],
                )
                logging.info("Comments count: %s", len(task_comments))
                for comment_data in task_comments:
                    comment_id = int(comment_data["gid"])
                    if comment_data["created_by"] is not None:
                        user_id = comment_data["created_by"]["gid"]
                        yield {
                            "user_id": user_id,
                            "comment_id": comment_id,
                            "task_id": task_id,
                        }


class LoadAdditionalInfoForComment:
    def __init__(self, asana_api_client: AsanaApiClient, asana_comment_prettifier: AsanaCommentPrettifier):
        self.asana_api_client = asana_api_client
        self.asana_comment_prettifier = asana_comment_prettifier

    def load(self, comment: AsanaComment) -> None:
        """Load comment data.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        task_data = self.asana_api_client.get_task(task_id=comment.task_id)
        comment_data = self.asana_api_client.get_comment(comment_id=comment.comment_id)
        pretty_comment_text = self.asana_comment_prettifier.prettify(comment_text=comment_data["text"])
        comment.task_url = task_data["permalink_url"]
        comment.text = pretty_comment_text
        comment.save()


@dataclass
class LoadAdditionalInfoForWebhookProject:
    asana_api_client: AsanaApiClient

    def load(self, webhook_project: AsanaWebhookProject) -> None:
        project_data = self.asana_api_client.get_project(
            project_id=webhook_project.project_id,
            opt_fields=["name", "permalink_url"],
        )
        webhook_project.project_name = project_data["name"]
        webhook_project.project_url = project_data["permalink_url"]
        webhook_project.save()


@dataclass
class LoadAdditionalInfoForProjectIgnoredSection:
    asana_api_client: AsanaApiClient

    def load(self, project_ignored_section: ProjectIgnoredSection) -> None:
        """Load project data.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        section_data = self.asana_api_client.get_section(project_ignored_section.section_id)
        project_ignored_section.section_name = section_data["name"]
        project_ignored_section.save()


@dataclass
class LoadCommentsAdditionalInfo:
    asana_api_client: AsanaApiClient

    def load(self, queryset: QuerySet[AsanaComment]) -> dict[str, int]:
        """Load comment info.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        comments_to_update = queryset.filter(
            Q(text="") | Q(task_url=""),
            is_deleted=False,
        )
        asana_users = AtlasUser.objects.all()
        profile_url_mention_map = get_user_profile_url_mention_map(asana_users=asana_users)
        asana_comment_prettifier = AsanaCommentPrettifier(profile_urls_mention_map=profile_url_mention_map)
        additional_info_comment_loader = LoadAdditionalInfoForComment(
            asana_api_client=self.asana_api_client,
            asana_comment_prettifier=asana_comment_prettifier,
        )
        success_updated = 0
        errors: list[str] = []
        for comment in comments_to_update:
            try:
                additional_info_comment_loader.load(comment=comment)
                success_updated += 1
            except AsanaApiClientError as error:
                errors.append(str(error))
        return {
            "success_updated": success_updated,
            "errors_count": len(errors),
        }


class SenderRegistrySynchronizer:
    @transaction.atomic
    def synchronize(self) -> dict[str, int]:
        sender_names_db = ProjectNotifySender.objects.values_list("name", flat=True)
        sender_names_register = list(SENDERS_REGISTRY)
        to_delete = set(sender_names_db) - set(sender_names_register)
        ProjectNotifySender.objects.filter(name__in=to_delete).delete()
        logging.info("Senders to delete: %s", to_delete)
        deleted = len(to_delete)
        new_created = 0
        updated = 0
        for sender_name, sender_info in SENDERS_REGISTRY.items():
            try:
                sender = ProjectNotifySender.objects.get(name=sender_name)
                sender.description = sender_info.description
                sender.save()
                updated += 1
            except ProjectNotifySender.DoesNotExist:
                ProjectNotifySender.objects.create(
                    name=sender_info.name,
                    description=sender_info.description,
                )
                new_created += 1
        result = {
            "deleted": deleted,
            "new_created": new_created,
            "updated": updated,
        }
        logging.info("Result: %s", result)
        return result
