from datetime import timedelta

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from asana.constants import (
    SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID,
    TECH_DIV_KVA_PROJECT_COMPLETE_SECTION_ID,
    AtlasProject,
)
from asana.models import AtlasUser
from asana.services import AsanaCommentPrettifier, get_user_profile_url_mention_map
from common import MessageSender
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import AsanaComment
from .services import AsanaCommentNotifier, FetchMissingProjectCommentsService, LoadAdditionalInfoForComment


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


class FetchCommentsAdditionalInfoUseCase:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self, queryset: QuerySet[AsanaComment]) -> dict:
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
