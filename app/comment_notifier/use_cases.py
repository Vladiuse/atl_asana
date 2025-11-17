import logging
from dataclasses import dataclass

from asana.client import AsanaApiClient
from common import MessageSender
from django.db import IntegrityError
from message_sender.tasks import send_log_message_task

from .models import AsanaComment, AsanaWebhookProject
from .senders import SourceProjectSender
from .services import AsanaCommentNotifier, ProjectCommentsGenerator


class AsanaCommentNotifierUseCase:
    MINUTES_AGO = 1

    def __init__(self, asana_api_client: AsanaApiClient, message_sender: MessageSender):
        self.asana_api_client = asana_api_client
        self.message_sender = message_sender

    def execute(self, comment_id) -> None:
        comment_notifier = AsanaCommentNotifier(
            asana_api_client=self.asana_api_client,
            message_sender=self.message_sender,
            comment_notifier=SourceProjectSender(message_sender=self.message_sender),
        )
        comment_notifier.process(comment_id=comment_id)


@dataclass
class FetchMissingProjectCommentsUseCase:
    asana_api_client: AsanaApiClient

    def execute(self) -> dict:
        from .tasks import notify_new_asana_comments_tasks

        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        use_case_result = {}
        exists_comment_ids = set(AsanaComment.objects.values_list("comment_id", flat=True))
        projects = AsanaWebhookProject.objects.prefetch_related("ignored_sections")
        project_comments_generator = ProjectCommentsGenerator(
            asana_api_client=self.asana_api_client,
        )
        errors_count = 0
        for project in projects:
            project_comments_count = 0
            for comment_data in project_comments_generator.generate(project=project):
                if comment_data["comment_id"] not in exists_comment_ids:
                    logging.info("find new comment: %s", comment_data["comment_id"])
                    try:
                        AsanaComment.objects.create(
                            user_id=comment_data["user_id"],
                            comment_id=comment_data["comment_id"],
                            task_id=comment_data["task_id"],
                            project=project,
                        )
                        project_comments_count += 1
                        notify_new_asana_comments_tasks.apply_async(args=[comment_data["comment_id"]], countdown=60)
                    except IntegrityError as error:
                        message = (
                            f"⚠️ {self.__class__.__name__}\n"
                            f"Cant save asana comment: {comment_data['comment_id']}\n"
                            f"{error}"
                        )
                        send_log_message_task.delay(message=message)
                        errors_count += 1
            use_case_result[str(project)] = project_comments_count
        use_case_result["errors_count"] = errors_count
        return use_case_result
