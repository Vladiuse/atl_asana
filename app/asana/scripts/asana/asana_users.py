import logging

from asana.client import AsanaApiClient
from asana.repository import AsanaUserRepository
from django.conf import settings

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
repository = AsanaUserRepository(api_client=asana_client)
logging.basicConfig(level=logging.INFO)


def run() -> None:
    repository.update_all()

