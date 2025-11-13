import logging
from datetime import timedelta

from asana.client import AsanaApiClient
from asana.client.exception import AsanaForbiddenError, AsanaNotFoundError
from asana.constants import (
    SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID,
    TECH_DIV_KVA_PROJECT_COMPLETE_SECTION_ID,
    AtlasProject,
)
from common import MessageSender
from django.db.models import QuerySet
from django.utils import timezone

from .models import AsanaComment
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
        fetch_missing_project_comments_service = FetchMissingProjectCommentsService(
            asana_api_client=self.asana_api_client,
        )
        source_div_project_result = fetch_missing_project_comments_service.execute(
            project_id=AtlasProject.SOURCE_DIV_PROBLEMS_REQUESTS.value,
            ignored_sections_ids=[
                SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID,
            ],
        )
        kva_tech_project_result = fetch_missing_project_comments_service.execute(
            project_id=AtlasProject.TECH_DIV_KVA.value,
            ignored_sections_ids=[TECH_DIV_KVA_PROJECT_COMPLETE_SECTION_ID],
        )
        return {
            "source_div_project_result": source_div_project_result,
            "kva_tech_project_result": kva_tech_project_result,
        }


class FetchCommentTaskUrls:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self) -> dict:
        tasks_ids_without_task_urls = (
            AsanaComment.objects.filter(task_url="", is_deleted=False).values_list("task_id", flat=True).distinct()
        )
        logging.info("comments_without_task_urls: %s", len(tasks_ids_without_task_urls))
        updated_tasks = 0
        deleted_tasks = 0
        for task_id in tasks_ids_without_task_urls:
            logging.info("Comment id: %s", task_id)
            try:
                task_data = self.asana_api_client.get_task(task_id=task_id)
                task_url = task_data["permalink_url"]
                AsanaComment.objects.filter(task_id=task_id).update(task_url=task_url)
                updated_tasks += 1
            except (AsanaForbiddenError, AsanaNotFoundError) as error:
                logging.info("Cant get task: %s", error)
                comment_models = AsanaComment.objects.filter(task_id=task_id)
                for comment_model in comment_models:
                    comment_model.mark_as_deleted()
                deleted_tasks += 1
        return {
            "updated_comments": updated_tasks,
            "deleted_tasks": deleted_tasks,
            "to_load": len(tasks_ids_without_task_urls),
        }
