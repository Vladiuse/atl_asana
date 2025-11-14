from datetime import timedelta

from asana.client import AsanaApiClient
from common import MessageSender
from django.db.models import QuerySet
from django.utils import timezone

from .models import AsanaComment, AsanaWebhookProject
from .services import AsanaCommentNotifier, FetchMissingProjectCommentsService


class AsanaCommentNotifierUseCase:
    MINUTES_AGO = 1

    def __init__(self, asana_api_client: AsanaApiClient, message_sender: MessageSender):
        self.asana_api_client = asana_api_client
        self.comment_notify_service = AsanaCommentNotifier(
            asana_api_client=asana_api_client,
            message_sender=message_sender,
        )

    def _get_comments_to_notify(self) -> QuerySet[AsanaComment]:
        cutoff = timezone.now() - timedelta(minutes=self.MINUTES_AGO)
        return AsanaComment.objects.filter(is_deleted=False, is_notified=None, created__lt=cutoff)

    def execute(self) -> dict:
        comments = self._get_comments_to_notify()
        for comment_model in comments:
            self.comment_notify_service.process(comment_id=comment_model.comment_id)
        return {"processed_comments": len(comments)}


class FetchMissingProjectCommentsUseCase:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self) -> dict:
        use_case_result = {}
        projects = AsanaWebhookProject.objects.prefetch_related("ignored_sections")
        for project in projects:
            fetch_missing_project_comments_service = FetchMissingProjectCommentsService(
                asana_api_client=self.asana_api_client,
            )
            result = fetch_missing_project_comments_service.execute(project=project)
            use_case_result[project.project_name] = result
        return use_case_result


