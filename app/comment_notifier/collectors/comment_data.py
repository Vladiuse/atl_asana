import logging

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from asana.models import AtlasUser
from asana.repository import AsanaUserRepository
from asana.services import AsanaCommentPrettifier, get_user_profile_url_mention_map
from asana.utils import get_asana_profile_url_by_id

from app.asana.constants import ATLAS_WORKSPACE_ID
from comment_notifier.models import AsanaComment
from comment_notifier.utils import extract_user_profile_id_from_text

from .dto import CommentDto
from .exceptions import CommentDeletedError


class CommentDataCollector:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client
        self.asana_users_repository = AsanaUserRepository(api_client=self.asana_api_client)

    def collect(self, comment_model: AsanaComment) -> CommentDto:
        try:
            task_data = self.asana_api_client.get_task(task_id=comment_model.task_id)
            comment_data = self.asana_api_client.get_comment(comment_id=comment_model.comment_id)
        except (AsanaForbiddenError, AsanaNotFoundError) as error:
            msg = f"Cant get access to comment {comment_model.comment_id}"
            raise CommentDeletedError(msg) from error
        logging.info("Raw comment text: %s", comment_data["text"])
        comment_mentions_profile_ids = extract_user_profile_id_from_text(text=comment_data["text"])
        mention_users: list[AtlasUser] = []
        profile_url_not_found_in_db: list[str] = []
        for profile_id in comment_mentions_profile_ids:
            try:
                asana_user = self.asana_users_repository.get(membership_id=profile_id)
                mention_users.append(asana_user)
            except AsanaApiClientError:
                logging.exception("AsanaApiClientError")
                profile_url = get_asana_profile_url_by_id(profile_id=profile_id, workspace_id=ATLAS_WORKSPACE_ID)
                profile_url_not_found_in_db.append(profile_url)
        profile_urls_mention_map = get_user_profile_url_mention_map(asana_users=AtlasUser.objects.all())
        asana_comment_prettifier = AsanaCommentPrettifier(profile_urls_mention_map=profile_urls_mention_map)
        pretty_comment_text = asana_comment_prettifier.prettify(comment_text=comment_data["text"])
        return CommentDto(
            comment_model=comment_model,
            comment_data=comment_data,
            task_data=task_data,
            mention_users=mention_users,
            pretty_comment_text=pretty_comment_text,
            mentions_profile_ids=comment_mentions_profile_ids,
            profile_url_not_found_in_db=profile_url_not_found_in_db,
        )
