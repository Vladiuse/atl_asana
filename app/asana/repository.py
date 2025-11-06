import logging

from asana.client import AsanaApiClient

from .constants import ATLAS_WORKSPACE_ID
from .models import AtlasUser


class AsanaUserRepository:
    def __init__(self, api_client: AsanaApiClient):
        self.api_client = api_client

    def get_user(self, membership_id: int) -> AtlasUser:
        try:
            user = AtlasUser.objects.get(membership_id=membership_id)
            logging.info("Get user from DB")
            return user
        except AtlasUser.DoesNotExist:
            logging.info("Try load user from asana")
            return self.create_by_membership_id(membership_id=membership_id)

    def update_all(self) -> None:
        atlas_memberships = self.api_client.get_workspace_memberships_for_workspace(workspace_id=ATLAS_WORKSPACE_ID)
        logging.info("Memberships in asana: %s", len(atlas_memberships))
        exist_memberships_in_db = [str(i) for i in AtlasUser.objects.values_list("atlas_profile_id", flat=True)]
        logging.info("Exists memberships ids: %s", exist_memberships_in_db)
        logging.info("Memberships in DB: %s", len(exist_memberships_in_db))
        for membership in atlas_memberships:
            if membership["gid"] not in exist_memberships_in_db:
                atlas_profile_id = membership["gid"]
                logging.info("Detect new Memberships: %s", atlas_profile_id)
                name = membership["user"]["name"]
                user_id = membership["user"]["gid"]
                user_data = self.api_client.get_user(user_id=user_id)
                email = user_data.get("email") or ""
                photo = user_data["photo"].get("image_128x128", "") if user_data["photo"] else ""
                AtlasUser.objects.create(
                    atlas_profile_id=atlas_profile_id,
                    name=name,
                    user_id=user_id,
                    avatar_url=photo,
                    email=email,
                )

    def create_by_membership_id(self, membership_id: int) -> AtlasUser:
        membership = self.api_client.get_workspace_membership(membership_id=membership_id)
        user_id = membership["user"]["gid"]
        user_data = self.api_client.get_user(user_id=user_id)
        atlas_profile_id = membership["gid"]
        name = membership["user"]["name"]
        email = user_data.get("email") or ""
        photo = user_data["photo"].get("image_128x128", "") if user_data["photo"] else ""
        return AtlasUser.objects.create(
            atlas_profile_id=atlas_profile_id,
            name=name,
            user_id=user_id,
            avatar_url=photo,
            email=email,
        )



