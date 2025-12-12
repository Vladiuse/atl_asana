from dataclasses import dataclass

from constance import config
from django.utils import timezone
from gspread import Client
from gspread.worksheet import JSONResponse

"""
EXAMPLE how to connet to google sheets
~~~~~~~~~~~~~~~~~

import gspread
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(
    settings.GOOGLE_CREDENTIALS_PATH,
    scopes=scopes,
)
client = gspread.authorize(credentials=creds)
sheet = client.open_by_key("1ztb8tw4nlT7Xk8FJAy_I-wXsWAggP_pKudXIDRVvSz8").worksheet(title="Лист1")
sheet.append_rows(
    values=[
        ["a", "b", "c"],
        ["d", "e", "f"],
    ],
)
"""


@dataclass
class CreativeDto:
    assignee: str
    bayer_code: str
    hook: str
    hold: str
    ctr: str
    task_name: str
    task_url: str
    status: str
    comment: str


class CreativeGoogleTable:
    def __init__(self, client: Client):
        self.client = client

    def _convert_creative_to_line(self, creative_dto: CreativeDto) -> list:
        return [
            timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
            creative_dto.task_name,
            creative_dto.task_url,
            creative_dto.assignee,
            creative_dto.bayer_code,
            creative_dto.hook,
            creative_dto.hold,
            creative_dto.ctr,
            creative_dto.status,
            creative_dto.comment,
        ]

    def add_creatives(self, creatives: list[CreativeDto]) -> JSONResponse:
        data_to_send = []
        for creative in creatives:
            data_to_send.append(self._convert_creative_to_line(creative_dto=creative))
        sheet = self.client.open_by_key(config.CREATIVE_GOOGLE_TABLE_ID).worksheet(title=config.CREATIVE_TABLE_LIST_NAME)
        json_response: JSONResponse = sheet.append_rows(values=data_to_send)
        return json_response
