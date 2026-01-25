from pprint import pprint

import gspread
from creative_quality.creative_table import CreativeDto, CreativeGoogleTable
from django.conf import settings
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
    settings.GOOGLE_CREDENTIALS_PATH,
    scopes=scopes,
)
client = gspread.authorize(credentials=credentials)
google_table = CreativeGoogleTable(client=client)


test_data = [
    CreativeDto(
        assignee="Иван Иванов",
        bayer_code="B123",
        hook=1,
        hold=1,
        ctr=1,
        task_name="Креатив №1",
        task_url="https://example.com/task/1",
        status="WAITING",
        comment="Первый тестовый креатив",
        country="AA",
        link_on_work="link on work",
        adaptive_name="XXX",
    ),
    CreativeDto(
        assignee="Мария Петрова",
        bayer_code="B456",
        hook=1,
        hold=1,
        ctr=1,
        task_name="Креатив №2",
        task_url="https://example.com/task/2",
        status="NEED_REVIEW",
        comment="Второй тестовый креатив",
        country="AA",
        link_on_work="link on work",
        adaptive_name="YYY",
    ),
    CreativeDto(
        assignee="Сергей Смирнов",
        bayer_code="B789",
        hook=1,
        hold=1,
        ctr=1,
        task_name="Креатив №3",
        task_url="https://example.com/task/3",
        status="RATED",
        comment="Третий тестовый креатив",
        country="AA",
        link_on_work="link on work",
        adaptive_name="ZZZ",
    ),
]

result = google_table.add_creatives(creatives=test_data)
pprint(result)
