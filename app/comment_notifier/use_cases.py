import logging
from datetime import timedelta

from asana.client import AsanaApiClient
from asana.client.exception import AsanaForbiddenError, AsanaNotFoundError
from asana.constants import SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID
from common import MessageSender
from django.db.models import QuerySet
from django.utils import timezone

from .models import AsanaComment
from .services import AsanaCommentNotifier, FetchMissingProjectCommentsService


class AsanaCommentNotifierUseCase:
    def __init__(self, asana_api_client: AsanaApiClient, message_sender: MessageSender):
        self.asana_api_client = asana_api_client
        self.comment_notify_service = AsanaCommentNotifier(
            asana_api_client=asana_api_client,
            message_sender=message_sender,
        )

    def _get_comments_to_notify(self) -> QuerySet[AsanaComment]:
        cutoff = timezone.now() - timedelta(minutes=5)
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
        fetch_missing_project_comments_service.execute(project_id=SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID, ignored_sections_ids=[])

    # def _get_project_active_sections(self) -> list[dict]:
    #     result = []
    #     sections = self.asana_api_client.get_project_sections(project_id=SOURCE_DIV_PROBLEMS_REQUESTS_PROJECT_ID)
    #     for section_data in sections:
    #         if section_data["gid"] not in self.DIV_PROJECT_IGNORED_SECTIONS:
    #             result.append(section_data)
    #     return result
    #
    # def execute(self) -> dict:
    #     new_comments_count = 0
    #     exists_comment_ids = set(AsanaComment.objects.values_list("comment_id", flat=True))
    #     logging.info("exists_comment_ids: %s", len(exists_comment_ids))
    #     sections = self._get_project_active_sections()
    #     for section_data in sections:
    #         section_tasks = self.asana_api_client.get_section_tasks(section_id=section_data["gid"])
    #         logging.info("section: %s, tasks: %s", section_data["name"], len(section_tasks))
    #         for task_data in section_tasks:
    #             task_id = task_data["gid"]
    #             logging.info("Task: %s %s", task_id, task_data["name"])
    #             task_comments = self.asana_api_client.get_comments_from_task(task_id=task_id)
    #             logging.info("Comments count: %s", len(task_comments))
    #             for comment_data in task_comments:
    #                 comment_id = int(comment_data["gid"])
    #                 if comment_data["created_by"] is not None:
    #                     user_id = comment_data["created_by"]["gid"]
    #                     if comment_id not in exists_comment_ids:
    #                         logging.info("find new comment: %s", comment_id)
    #                         AsanaComment.objects.create(
    #                             user_id=user_id,
    #                             comment_id=comment_id,
    #                             task_id=task_id,
    #                         )
    #                         new_comments_count += 1
    #     logging.info("new_comments_count: %s", new_comments_count)
    #     return {"new_comments_count": new_comments_count}


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
