import logging
from dataclasses import dataclass
from time import sleep
from typing import Callable

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from asana.constants import Position
from asana.models import AtlasUser
from asana.repository import AsanaUserRepository
from asana.services import AsanaCommentPrettifier, get_user_profile_url_mention_map
from asana.utils import get_asana_profile_url_by_id
from common import MessageSender
from common.message_sender import UserTag
from common.utils import normalize_multiline

from .models import AsanaComment, AsanaWebhookRequestData
from .utils import extract_user_profile_id_from_text


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

    def _event_to_comment_dto(self, events_data: dict) -> list[AsanaNewCommentEvent]:
        result = []
        for event in events_data["events"]:
            if event["resource"]["resource_subtype"] == "comment_added":
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
            )
        asana_webhook.is_target_event = bool(asana_comments_dto)
        asana_webhook.save()
        return ProcessAsanaNewCommentEvent.Result(
            created_comments_count=len(asana_comments_dto),
            comments=asana_comments_dto,
        )


@dataclass
class CommentDto:
    comment_model: AsanaComment
    comment_data: dict
    task_data: dict
    pretty_comment_text: str
    mention_users: list[AtlasUser]

    @property
    def has_mention(self) -> bool:
        return bool(self.mention_users)


class AsanaSourceProjectCommentMessageSender:
    def __init__(
        self,
        message_sender: MessageSender,
        # asana_comment_prettifier: AsanaCommentPrettifier,
    ):
        self.message_sender = message_sender
        # self.asana_comment_prettifier = asana_comment_prettifier

    def _get_notifier_func(self, asana_user: AtlasUser) -> Callable[[AtlasUser, CommentDto], dict | None]:
        if not all([asana_user.messenger_code, asana_user.position]):
            return self._notify_cant_send_message

        registry: dict[Position, Callable[[AtlasUser, CommentDto], dict | None]] = {
            Position.FARMER: self._notify_farmer,
            Position.MANAGER: self._notify_baer_or_manager,
            Position.BUYER: self._notify_baer_or_manager,
        }

        return registry.get(asana_user.position, self._notify_not_target_position)

    def _notify_farmer(self, asana_user: AtlasUser, comment_dto: CommentDto) -> dict:
        task_url = comment_dto.task_data["permalink_url"]
        task_name = comment_dto.task_data["name"]
        message = f"""
            {task_name}
            Task url: {task_url}
            Comment:
            {comment_dto.pretty_comment_text}
            """
        message = normalize_multiline(message)
        return self.message_sender.send_message_to_user(
            user_tags=[UserTag(asana_user.messenger_code)],
            message=message,
        )

    def _notify_baer_or_manager(self, asana_user: AtlasUser, comment_dto: CommentDto) -> dict:
        task_name = comment_dto.task_data["name"]
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
            {task_name}
            Task url: {task_url}
            Comment:
            {comment_dto.pretty_comment_text}
            """
        message = normalize_multiline(message)
        return self.message_sender.send_message_to_user(
            user_tags=[UserTag(asana_user.messenger_code)],
            message=message,
        )

    def _notify_not_target_position(self, asana_user: AtlasUser,  comment_dto: CommentDto) -> None:
        pass

    def _notify_cant_send_message(self, asana_user: AtlasUser,  comment_dto: CommentDto) -> None:
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
            ⚠️ Упомянут пользователь без должности или тэга мессенджера.
            
            Пользователь:
            Id: {asana_user.user_id}
            Name: {asana_user.name}
            Email: {asana_user.email}
            Task url: {task_url}
        """
        message = normalize_multiline(message)
        self.message_sender.send_message(handler=MessageSender.KVA_USER, message=message)

    def send_message_to_users(self, comment_dto: CommentDto) -> None:
        for asana_user in comment_dto.mention_users:
            notifier_func = self._get_notifier_func(asana_user=asana_user)
            logging.info("Notify func: %s", notifier_func.__name__)
            message_send_result = notifier_func(asana_user=asana_user, comment_dto=comment_dto)  # type: ignore[arg-type]
            logging.info("message_send_result: %s", message_send_result)


class AsanaCommentNotifier:
    def __init__(
        self,
        asana_api_client: AsanaApiClient,
        message_sender: MessageSender,
    ):
        self.asana_api_client = asana_api_client
        self.asana_users_repository = AsanaUserRepository(api_client=self.asana_api_client)
        self.message_sender = message_sender

    def _save_task_url(self, comment: AsanaComment, task_data: dict) -> None:
        comment.task_url = task_data["permalink_url"]
        comment.save()

    def _process_no_mentions_comment(self, comment: AsanaComment) -> None:
        comment.has_mention = False
        comment.is_notified = False
        comment.save()

    def _process_comment_with_mentions(self, comment: AsanaComment) -> None:
        comment.has_mention = True
        comment.is_notified = True
        comment.save()

    def _notify_profiles_not_found(self, profiles: list[str], task_data: dict) -> None:
        if len(profiles) != 0:
            task_url = task_data["permalink_url"]
            message = f"Not found asana user for profiles: {profiles}\nTask url: {task_url}"
            self.message_sender.send_message(handler=MessageSender.KVA_USER, message=message)

    def process(self, comment_id: int) -> None:
        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        logging.info("AsanaCommentNotifier comment_id: %s", comment_id)
        comment_model = AsanaComment.objects.get(comment_id=comment_id)
        try:
            task_data = self.asana_api_client.get_task(task_id=comment_model.task_id)
            comment_data = self.asana_api_client.get_comment(comment_id=comment_id)
        except (AsanaForbiddenError, AsanaNotFoundError):
            comment_model.mark_as_deleted()
            logging.info("comment_id %s deleted", comment_id)
            return
        logging.info("Raw comment text: %s", comment_data["text"])
        self._save_task_url(comment=comment_model, task_data=task_data)
        comment_mentions_profile_ids = extract_user_profile_id_from_text(text=comment_data["text"])
        if len(comment_mentions_profile_ids) == 0:
            self._process_no_mentions_comment(comment=comment_model)
            logging.info("Mentions not found for comment")
        else:
            mention_users: list[AtlasUser] = []
            users_profile_url_not_found_in_db: list[str] = []
            for profile_id in comment_mentions_profile_ids:
                try:
                    asana_user = self.asana_users_repository.get(membership_id=profile_id)
                    mention_users.append(asana_user)
                except AsanaApiClientError as error:
                    logging.error("AsanaApiClientError: %s", error)
                    profile_url = get_asana_profile_url_by_id(profile_id=profile_id)
                    users_profile_url_not_found_in_db.append(profile_url)
            self._notify_profiles_not_found(
                profiles=users_profile_url_not_found_in_db,
                task_data=task_data,
            )

            profile_urls_mention_map = get_user_profile_url_mention_map(asana_users=AtlasUser.objects.all())
            asana_comment_prettifier = AsanaCommentPrettifier(profile_urls_mention_map=profile_urls_mention_map)
            pretty_comment_text = asana_comment_prettifier.prettify(comment_text=comment_data["text"])
            comment_dto = CommentDto(
                comment_model=comment_model,
                comment_data=comment_data,
                task_data=task_data,
                mention_users=mention_users,
                pretty_comment_text=pretty_comment_text,
            )
            asana_comment_message_sender = AsanaSourceProjectCommentMessageSender(
                message_sender=self.message_sender,
            )
            asana_comment_message_sender.send_message_to_users(comment_dto=comment_dto)
            self._process_comment_with_mentions(comment=comment_model)


class FetchMissingProjectCommentsService:
    """
    Search comments in tasks in projects that not in DB. If you find - save it.
    In projects cant be ignored sections.
    """

    SLEEP_AFTER_FETCH_TASK = 0.2

    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def _get_project_active_sections(
        self,
        project_id: str,
        ignored_sections_ids: list[int] | None = None,
    ) -> list[dict]:
        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        result = []
        if ignored_sections_ids is None:
            ignored_sections_ids = []
        sections = self.asana_api_client.get_project_sections(project_id=project_id)
        for section_data in sections:
            if section_data["gid"] not in ignored_sections_ids:
                result.append(section_data)
        return result

    def execute(self, project_id: str, ignored_sections_ids: list[str] | None = None) -> dict:
        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        logging.info(
            "FetchMissingProjectCommentsService: project_id: %s, ignored_sections_ids: %s",
            project_id,
            ignored_sections_ids,
        )
        new_comments_count = 0
        exists_comment_ids = set(AsanaComment.objects.values_list("comment_id", flat=True))
        logging.info("exists_comment_ids: %s", len(exists_comment_ids))
        sections = self._get_project_active_sections(project_id=project_id, ignored_sections_ids=ignored_sections_ids)
        logging.info("Sections to collect comments: %s", sections)
        for section_data in sections:
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
                        if comment_id not in exists_comment_ids:
                            logging.info("find new comment: %s", comment_id)
                            AsanaComment.objects.create(
                                user_id=user_id,
                                comment_id=comment_id,
                                task_id=task_id,
                            )
                            new_comments_count += 1
        logging.info("new_comments_count: %s", new_comments_count)
        section_names = [section_data["name"] for section_data in sections]
        return {"new_comments_count": new_comments_count, "sections": section_names}


class LoadAdditionalInfoForComment:
    def __init__(self, asana_api_client: AsanaApiClient, asana_comment_prettifier: AsanaCommentPrettifier):
        self.asana_api_client = asana_api_client
        self.asana_comment_prettifier = asana_comment_prettifier

    def load(self, comment: AsanaComment) -> None:
        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        task_data = self.asana_api_client.get_task(task_id=comment.task_id)
        comment_data = self.asana_api_client.get_comment(comment_id=comment.comment_id)
        pretty_comment_text = self.asana_comment_prettifier.prettify(comment_text=comment_data["text"])
        comment.task_url = task_data["permalink_url"]
        comment.text = pretty_comment_text
        comment.save()
