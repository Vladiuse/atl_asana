import logging

from common.exception import AppExceptionError

from asana.client import AsanaApiClient

from .constants import ATLAS_WORKSPACE_ID
from .models import AtlasUser


class AsanaUserRepository:
    def __init__(self, api_client: AsanaApiClient):
        self.api_client = api_client

    def _create_user_by_data(self, *, membership_data: dict, user_data: dict) -> AtlasUser:
        user_id = user_data["gid"]
        membership_id = membership_data["gid"]
        name = membership_data["user"]["name"]
        email = user_data.get("email") or ""
        photo = user_data["photo"].get("image_128x128", "") if user_data["photo"] else ""
        return AtlasUser.objects.create(
            membership_id=membership_id,
            name=name,
            user_id=user_id,
            avatar_url=photo,
            email=email,
        )

    def _create_by_membership_id(self, membership_id: int) -> AtlasUser:
        """Create user by membership_id.

        Raises:
             AsanaApiClientError: if cant get data from asana

        """
        membership_data = self.api_client.get_workspace_membership(membership_id=membership_id)
        user_data = self.api_client.get_user(user_id=membership_data["user"]["gid"])
        return self._create_user_by_data(membership_data=membership_data, user_data=user_data)

    def _create_by_user_id(self, user_id: int) -> AtlasUser:
        """Create AtlasUser by id.

        Raises:
            AsanaApiClientError: if cant get data from asana

        """
        user_data = self.api_client.get_user(user_id=user_id)
        atlas_user_membership_id = None
        user_memberships = self.api_client.get_workspace_memberships_for_user(user_id=user_id)
        logging.info("user_memberships: %s", user_memberships)
        for membership_data in user_memberships:
            if membership_data["workspace"]["gid"] == str(ATLAS_WORKSPACE_ID):
                atlas_user_membership_id = membership_data["gid"]
                break
        if atlas_user_membership_id is None:
            msg = f"Cant find Atlas membership for user: {user_id}"
            raise AppExceptionError(msg)
        membership_data = self.api_client.get_workspace_membership(membership_id=atlas_user_membership_id)
        return self._create_user_by_data(membership_data=membership_data, user_data=user_data)

    def get(
        self,
        *,
        membership_id: int | None = None,
        user_id: int | None = None,
    ) -> AtlasUser:
        """Get user by usr_id or membership_id.

        Raises:
             AsanaApiClientError: if cant get data from asana

        """
        if membership_id is None and user_id is None:
            msg = "Either membership_id or user_id must be provided"
            raise ValueError(msg)
        try:
            if membership_id is not None:
                user = AtlasUser.objects.get(membership_id=membership_id)
                logging.info("Get user from DB by membership_id")
            else:
                user = AtlasUser.objects.get(user_id=user_id)
                logging.info("Get user from DB by user_id")
        except AtlasUser.DoesNotExist:
            if membership_id is not None:
                logging.info("Try load user from Asana by membership_id")
                return self._create_by_membership_id(membership_id=membership_id)
            logging.info("Try load user from Asana by user_id")
            assert user_id is not None  # noqa: S101
            return self._create_by_user_id(user_id=user_id)
        else:
            return user

    def update_all(self) -> dict[str, int]:
        """Update all users.

        Raises:
             AsanaApiClientError: if cant get data from asana

        """
        atlas_asana_memberships = self.api_client.get_workspace_memberships_for_workspace(
            workspace_id=ATLAS_WORKSPACE_ID,
        )
        logging.info("Memberships in asana: %s", len(atlas_asana_memberships))
        exist_memberships_in_db = [str(i) for i in AtlasUser.objects.values_list("membership_id", flat=True)]
        logging.info("Memberships in DB: %s", len(exist_memberships_in_db))
        new_created = 0
        for membership_data in atlas_asana_memberships:
            membership_id = membership_data["gid"]
            if membership_data["gid"] not in exist_memberships_in_db:
                logging.info("Detect new Memberships: %s", membership_id)
                user_data = self.api_client.get_user(user_id=membership_data["user"]["gid"])
                self._create_user_by_data(membership_data=membership_data, user_data=user_data)
                new_created += 1
        logging.info("New created: %s", new_created)
        return {"new_created": new_created}
