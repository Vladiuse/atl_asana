import logging
from dataclasses import dataclass

from asana.client import AsanaApiClient
from common import MessageSender
from django.db import IntegrityError
from message_sender.tasks import send_log_message_task

from .exceptions import NoSenderClassInProject
from .models import AsanaComment, AsanaWebhookProject, ProjectNotifySender
from .senders.registry import SENDERS_REGISTRY
from .services import AsanaCommentNotifier, ProjectCommentsGenerator


@dataclass
class AsanaCommentNotifierUseCase:
    asana_api_client: AsanaApiClient
    message_sender: MessageSender

    def execute(self, comment_id) -> None:
        logging.info("AsanaCommentNotifier comment_id: %s", comment_id)
        comment_model = AsanaComment.objects.get(comment_id=comment_id)
        project: AsanaWebhookProject = comment_model.project
        if project.message_sender is None:
            from message_sender.tasks import send_log_message_task

            message = f"🛑 {self.__class__.__name__}\nSet {ProjectNotifySender.__name__} for project: {project}"
            send_log_message_task.delay(message=message)
            raise NoSenderClassInProject(message)
        project_message_sender = SENDERS_REGISTRY[project.message_sender.name].sender
        comment_notifier = AsanaCommentNotifier(
            asana_api_client=self.asana_api_client,
            message_sender=self.message_sender,
            comment_notifier=project_message_sender(message_sender=self.message_sender),
        )
        comment_notifier.process(comment_model=comment_model)


@dataclass
class FetchMissingProjectCommentsUseCase:
    asana_api_client: AsanaApiClient

    def execute(self, send_messages: bool = True) -> dict:
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
        missing_comments_found:list[str] = []
        for project in projects:
            project_comments_count = 0
            for comment_data in project_comments_generator.generate(project=project):
                if str(comment_data["comment_id"]) not in exists_comment_ids:
                    logging.info("find new comment: %s", comment_data["comment_id"])
                    try:
                        AsanaComment.objects.create(
                            user_id=comment_data["user_id"],
                            comment_id=comment_data["comment_id"],
                            task_id=comment_data["task_id"],
                            project=project,
                        )
                        project_comments_count += 1
                        if send_messages:
                            notify_new_asana_comments_tasks.apply_async(
                                args=[comment_data["comment_id"]], countdown=60,
                            )
                            missing_comments_found.append(comment_data["comment_id"])
                    except IntegrityError as error:
                        logging.warning("IntegrityError save comment: %s", comment_data)
                        message = (
                            f"⚠️ {self.__class__.__name__}\n"
                            f"Cant save asana comment: {comment_data}\n"
                            f"{error}"
                        )
                        send_log_message_task.delay(message=message)
                        errors_count += 1
            use_case_result[str(project)] = project_comments_count
        if missing_comments_found:
            message = f"⚠️ Missing comments found: {missing_comments_found}"
            send_log_message_task.delay(message=message)
        use_case_result["errors_count"] = errors_count
        return use_case_result
