import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import requests
from common.exception import AppExceptionError
from django.core.files.base import ContentFile
from message_sender.models import AtlasUser
from requests.exceptions import RequestException

from asana.client import AsanaApiClient

from .constants import ATLAS_WORKSPACE_ID
from .models import AtlasAsanaUser
from .services import map_messenger_position_to_asana
from .utils import clean_user_avatar_url

logger = logging.getLogger(__name__)


@dataclass(frozen=False)
class AsanaUserDTO:
    membership_id: str
    name: str
    user_id: str
    email: str
    photo_url: str | None

    @classmethod
    def from_api(cls, *, membership_data: dict[str, Any], user_data: dict[str, Any]) -> "AsanaUserDTO":
        photo_url = user_data["photo"].get("image_128x128") if user_data["photo"] else None
        return cls(
            membership_id=membership_data["gid"],
            name=membership_data["user"]["name"],
            user_id=user_data["gid"],
            email=user_data.get("email") or "",
            photo_url=photo_url,
        )


class AvatarService:
    """Download asana avatar by url for asana user model."""

    def _download_avatar(self, url: str) -> ContentFile:  # type: ignore[type-arg]
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return ContentFile(resp.content)

    def load(self, asana_user: AtlasAsanaUser) -> bool:
        is_avatar_update = False
        if asana_user.avatar_url:
            try:
                avatar_file = self._download_avatar(url=asana_user.avatar_url)
            except RequestException:
                logger.exception("Cant load avatar for asana user %s, url: %s", asana_user, asana_user.avatar_url)
            else:
                filename = f"{asana_user.user_id}.png"
                asana_user.avatar.save(
                    filename,
                    avatar_file,
                    save=False,
                )
                asana_user.loaded_avatar_url = asana_user.avatar_url
                asana_user.save()
                is_avatar_update = True
        return is_avatar_update

    def delete(self, asana_user: AtlasAsanaUser) -> None:
        asana_user.avatar.delete(save=False)
        asana_user.loaded_avatar_url = ""
        asana_user.save()


class AsanaUserRepository:
    @dataclass(frozen=True)
    class UpdateUsersResult:
        created_user_ids: list[int]
        created_count: int
        deleted_count: int

    class AvatarSyncAction(Enum):
        UPDATE = "update"
        LOAD = "load"
        DELETE = "delete"
        NOTHING = "nothing"

    def __init__(self, api_client: AsanaApiClient):
        self.api_client = api_client
        self.avatar_service = AvatarService()

    def get_avatar_sync_action(self, user: AtlasAsanaUser, user_dto: AsanaUserDTO) -> AvatarSyncAction:
        # TODO: not user api url, check url from model field
        db_url: str | None = user.loaded_avatar_url
        api_url: str | None = user_dto.photo_url

        # asana avatar not exist
        if api_url is None:
            if db_url:
                return self.AvatarSyncAction.DELETE
            return self.AvatarSyncAction.NOTHING

        # asana avatar exist
        if not db_url:
            return self.AvatarSyncAction.LOAD

        # not equal urls
        if clean_user_avatar_url(db_url) != clean_user_avatar_url(api_url):
            return self.AvatarSyncAction.UPDATE

        return self.AvatarSyncAction.NOTHING

    def _create_user(self, user_dto: AsanaUserDTO) -> AtlasAsanaUser:
        try:
            owner = AtlasUser.objects.get(email=user_dto.email)
            position = map_messenger_position_to_asana(messenger_position=owner.role)
        except AtlasUser.DoesNotExist:
            owner = None
            position = None
        return AtlasAsanaUser.objects.create(
            membership_id=user_dto.membership_id,
            name=user_dto.name,
            user_id=user_dto.user_id,
            avatar_url=user_dto.photo_url if user_dto.photo_url else "",
            email=user_dto.email,
            owner=owner,
            position=position if position else "",
        )

    def _update_user(self, user: AtlasAsanaUser, user_dto: AsanaUserDTO) -> AtlasAsanaUser:
        user.name = user_dto.name
        user.email = user_dto.email
        user.avatar_url = user_dto.photo_url if user_dto.photo_url else ""
        try:
            owner = AtlasUser.objects.get(email=user_dto.email)
            position = map_messenger_position_to_asana(messenger_position=owner.role)
        except AtlasUser.DoesNotExist:
            owner = None
            position = None
        user.owner = owner
        user.position = position if position else ""
        user.save()
        return user

    def _create_by_membership_id(self, membership_id: str) -> AtlasAsanaUser:
        """Create user by membership_id.

        Raises:
             AsanaApiClientError: if cant get data from asana

        """
        membership_data = self.api_client.get_workspace_membership(membership_id=membership_id)
        user_data = self.api_client.get_user(user_id=membership_data["user"]["gid"])
        user_dto = AsanaUserDTO.from_api(
            membership_data=membership_data,
            user_data=user_data,
        )
        return self._create_user(user_dto=user_dto)

    def _create_by_user_id(self, user_id: str) -> AtlasAsanaUser:
        """Create AtlasUser by id.

        Raises:
            AsanaApiClientError: if cant get data from asana

        """
        user_data = self.api_client.get_user(user_id=user_id)
        atlas_user_membership_id = None
        user_memberships = self.api_client.get_workspace_memberships_for_user(user_id=user_id)
        logger.info("user_memberships: %s", user_memberships)
        for membership_data in user_memberships:
            if membership_data["workspace"]["gid"] == str(ATLAS_WORKSPACE_ID):
                atlas_user_membership_id = membership_data["gid"]
                break
        if atlas_user_membership_id is None:
            msg = f"Cant find Atlas membership for user: {user_id}"
            raise AppExceptionError(msg)
        membership_data = self.api_client.get_workspace_membership(membership_id=atlas_user_membership_id)
        user_dto = AsanaUserDTO.from_api(
            membership_data=membership_data,
            user_data=user_data,
        )
        return self._create_user(user_dto=user_dto)

    def get(
        self,
        *,
        membership_id: str | None = None,
        user_id: str | None = None,
    ) -> AtlasAsanaUser:
        """Get user by usr_id or membership_id.

        Raises:
             AsanaApiClientError: if cant get data from asana

        """
        if membership_id is None and user_id is None:
            msg = "Either membership_id or user_id must be provided"
            raise ValueError(msg)
        try:
            if membership_id is not None:
                user = AtlasAsanaUser.objects.get(membership_id=membership_id)
                logger.info("Get user from DB by membership_id")
            else:
                user = AtlasAsanaUser.objects.get(user_id=user_id)
                logger.info("Get user from DB by user_id")
        except AtlasAsanaUser.DoesNotExist:
            if membership_id is not None:
                logger.info("Try load user from Asana by membership_id")
                return self._create_by_membership_id(membership_id=membership_id)
            logger.info("Try load user from Asana by user_id")
            assert user_id is not None  # noqa: S101
            return self._create_by_user_id(user_id=user_id)
        else:
            return user

    def update_all(self) -> UpdateUsersResult:
        """Update all users.

        Raises:
             AsanaApiClientError: if cant get data from asana

        """
        atlas_asana_memberships = self.api_client.get_workspace_memberships_for_workspace(
            workspace_id=ATLAS_WORKSPACE_ID,
        )
        logger.info("Memberships in asana: %s", len(atlas_asana_memberships))
        exist_memberships_in_db = [str(i) for i in AtlasAsanaUser.objects.values_list("membership_id", flat=True)]
        actual_memberships_ids: set[str] = {membership_data["gid"] for membership_data in atlas_asana_memberships}
        deleted_count, deleted_by_model = AtlasAsanaUser.objects.exclude(
            membership_id__in=actual_memberships_ids,
        ).delete()
        logger.info("Deleted: %s", deleted_count)
        logger.info("Memberships in DB: %s", len(exist_memberships_in_db))
        created_ids: list[int] = []
        updated_ids: list[int] = []
        for membership_data in atlas_asana_memberships:
            membership_id = membership_data["gid"]
            user_data = self.api_client.get_user(user_id=membership_data["user"]["gid"])
            user_dto = AsanaUserDTO.from_api(
                membership_data=membership_data,
                user_data=user_data,
            )
            if membership_data["gid"] not in exist_memberships_in_db:
                # create user
                logger.info("Detect new Memberships: %s", membership_id)
                user = self._create_user(user_dto=user_dto)
                created_ids.append(user.pk)
                self.avatar_service.load(asana_user=user)
            else:
                # update exist user
                logger.info("Update Memberships: %s", membership_id)
                user = AtlasAsanaUser.objects.get(membership_id=membership_data["gid"])
                avatar_action = self.get_avatar_sync_action(user=user, user_dto=user_dto)
                logger.info("Avatar action: %s", avatar_action)
                user = self._update_user(user=user, user_dto=user_dto)
                updated_ids.append(user.pk)
                if avatar_action in (self.AvatarSyncAction.UPDATE, self.AvatarSyncAction.LOAD):
                    logger.info("Need load new avatar for user %s", user)
                    self.avatar_service.load(asana_user=user)
                if avatar_action == self.AvatarSyncAction.DELETE:
                    logger.info("Need delete avatar for user %s", user)
                    self.avatar_service.delete(asana_user=user)

        logger.info("New created: %s", len(created_ids))
        logger.info("Updated: %s", len(updated_ids))
        return self.UpdateUsersResult(
            created_user_ids=created_ids,
            created_count=len(created_ids),
            deleted_count=deleted_count,
        )
