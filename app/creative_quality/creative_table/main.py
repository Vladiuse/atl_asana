from dataclasses import dataclass

from constance import config
from django.utils import timezone
from gspread import Client, Spreadsheet, Worksheet
from gspread.exceptions import WorksheetNotFound
from gspread.worksheet import JSONResponse

"""
EXAMPLE how to connect to google sheets
~~~~~~~~~~~~~~~~~

import gspread
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(
    settings.GOOGLE_CREDENTIALS_PATH,
    scopes=scopes,
)
client = gspread.authorize(credentials=credentials)
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
    country: str
    assignee: str
    bayer_code: str
    hook: float
    hold: float
    ctr: float
    task_name: str
    task_url: str
    status: str
    comment: str
    link_on_work: str


class CreativeGoogleTable:
    def __init__(self, client: Client):
        self.client = client

    def _get_header_row(self) -> list[str]:
        return [
            "Дата",
            "Страна",
            "Task",
            "Url",
            "Ссылка на работу",
            "Исполнитель",
            "Баер",
            "Hook %",
            "Hold %",
            "CTR %",
            "Статус",
            "Комментарий",
            "Прим. от дизайнера",
        ]

    def _convert_creative_to_line(self, creative_dto: CreativeDto) -> list[str | int | float]:
        return [
            timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
            creative_dto.country,
            creative_dto.task_name,
            creative_dto.task_url,
            creative_dto.link_on_work,
            creative_dto.assignee,
            creative_dto.bayer_code,
            creative_dto.hook,
            creative_dto.hold,
            creative_dto.ctr,
            creative_dto.status,
            creative_dto.comment,
        ]

    def _create_new_sheet(self, spreadsheet: Spreadsheet, name: str) -> Worksheet:
        sheet = spreadsheet.add_worksheet(title=name, rows=100, cols=1)
        header_row = self._get_header_row()
        sheet.append_row(header_row)
        sheet.format(
            "A1:M1",
            {
                "backgroundColor": {"red": 0.7137, "green": 0.8431, "blue": 0.6588},
                "textFormat": {"bold": True},
            },
        )
        sheet.insert_row([], index=2)
        sheet.format(
            "A2:M2",
            {
                "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                "textFormat": {"bold": False},
            },
        )
        return sheet

    def _get_or_create_sheet(self) -> Worksheet:
        sheet_name = timezone.now().strftime("%m.%y")
        spreadsheet = self.client.open_by_key(config.CREATIVE_GOOGLE_TABLE_ID)
        try:
            sheet = spreadsheet.worksheet(
                title=sheet_name,
            )
        except WorksheetNotFound:
            sheet = self._create_new_sheet(spreadsheet=spreadsheet, name=sheet_name)
        return sheet

    def add_creatives(self, creatives: list[CreativeDto]) -> JSONResponse:
        """Add line with data to table.

        Raises:
             GSpreadException

        """
        data_to_send = [self._convert_creative_to_line(creative_dto=creative) for creative in creatives]
        sheet = self._get_or_create_sheet()
        json_response: JSONResponse = sheet.append_rows(values=data_to_send)
        return json_response
