import logging
from pprint import pprint

from asana.client import AsanaApiClient
from asana.repository import AsanaUserRepository
from django.conf import settings

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
logging.basicConfig(level=logging.INFO)
repository = AsanaUserRepository(api_client=asana_client)


def run() -> None:
    res = asana_client.get_project_sections(1199190886721558)
    pprint(res)
