import gspread
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(
    "service_account.json",
    scopes=scopes,
)
client = gspread.authorize(credentials=credentials)
sheet = client.open_by_key("1ztb8tw4nlT7Xk8FJAy_I-wXsWAggP_pKudXIDRVvSz8").worksheet("new")
sheet.append_row([1, 2, 3, 4])
sheet.format(
    f"A1:M1",
    {
        "backgroundColor": {"red": 0.7137, "green": 0.8431, "blue": 0.6588},
        "textFormat": {"bold": True},
    },
)
# spread = client.open_by_key("1ztb8tw4nlT7Xk8FJAy_I-wXsWAggP_pKudXIDRVvSz8")
# res = spread.add_worksheet(title="new", rows=1, cols=1)
# print(res)


# gspread.exceptions.WorksheetNotFound: Лист11
