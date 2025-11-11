import logging

from asana.client import AsanaApiClient
from asana.constants import SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID, SOURCE_DIV_PROBLEMS_REQUESTS_PROJECT_ID

from .models import AsanaComment


class AsanaCommentNotifierUseCase:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self) -> None:
        pass


class FetchMissingProjectCommentsUseCase:
    DIV_PROJECT_IGNORED_SECTIONS = [
        str(SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID),
    ]

    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def _project_active_sections(self) -> list[dict]:
        result = []
        sections = self.asana_api_client.get_project_sections(project_id=SOURCE_DIV_PROBLEMS_REQUESTS_PROJECT_ID)
        for section_data in sections:
            if section_data["gid"] not in self.DIV_PROJECT_IGNORED_SECTIONS:
                result.append(section_data)
        return result

    def execute(self) -> None:
        new_comments_count = 0
        exists_comment_ids = set(AsanaComment.objects.values_list("comment_id", flat=True))
        logging.info("exists_comment_ids: %s", len(exists_comment_ids))
        sections = self._project_active_sections()
        for section_data in sections:
            section_tasks = self.asana_api_client.get_section_tasks(section_id=section_data["gid"])
            logging.info("section: %s, tasks: %s", section_data["name"], len(section_tasks))
            for task_data in section_tasks:
                task_id = task_data["gid"]
                logging.info("Task: %s %s", task_id, task_data["name"])
                task_comments = self.asana_api_client.get_comments_from_task(task_id=task_id)
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
        print(new_comments_count)
