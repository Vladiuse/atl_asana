import logging

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

    def get_user(self, membership_id: int) -> AtlasUser:
        try:
            user = AtlasUser.objects.get(membership_id=membership_id)
            logging.info("Get user from DB")
            return user
        except AtlasUser.DoesNotExist:
            logging.info("Try load user from asana")
            return self.create_by_membership_id(membership_id=membership_id)

    def update_all(self) -> None:
        atlas_asana_memberships = self.api_client.get_workspace_memberships_for_workspace(workspace_id=ATLAS_WORKSPACE_ID)
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
                new_created+= 1
        logging.info("New created: %s", new_created)

    def create_by_membership_id(self, membership_id: int) -> AtlasUser:
        membership_data = self.api_client.get_workspace_membership(membership_id=membership_id)
        user_data = self.api_client.get_user(user_id=membership_data["user"]["gid"])
        return self._create_user_by_data(membership_data=membership_data, user_data=user_data)



