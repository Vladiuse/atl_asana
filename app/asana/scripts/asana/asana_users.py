from pprint import pprint
import logging
import json
from django.conf import settings
from asana.client import AsanaApiClient
from asana.constants import ATLAS_WORKSPACE_ID
from asana.repository import AsanaUserRepository

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
repository = AsanaUserRepository(api_client=asana_client)
logging.basicConfig(level=logging.INFO)


def run() -> None:
    repository.update_all()
    # repository.create_by_membership_id(membership_id=1210393628043137)
