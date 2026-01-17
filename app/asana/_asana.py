# ruff: noqa: T201, T203, ERA001, S113
from pprint import pprint

import requests

host = "atl-asana.vim-store.ru"
url = "https://atl-asana.vim-store.ru/asana/webhook/land/"


ASANA_KEY = "2/1205811800628284/1210753891941219:77e961a8e8594097a5c9fff330d00ae1"
TECH_PROJECT_ID = "1210393628043121"  # TECH
LAND_PROJECT_ID = "1202274282527282"


headers = {
    "Authorization": f"Bearer {ASANA_KEY}",
}


def create_webhook() -> None:
    data = {
        "data": {
            "target": "https://atl-asana.vim-store.ru/asana/webhook/vga-design-progect-add-task/",
            "resource": "1199190886721558",
            "filters": [
                # {"action": "added", "resource_type": "story"},
                {"action": "added", "resource_type": "task"},
            ],
        },
    }
    res = requests.post("https://app.asana.com/api/1.0/webhooks", headers=headers, json=data)
    print(res.status_code)
    pprint(res.json())


def get_webhooks() -> None:
    params: dict[str, str]  = {
        "workspace": "1167322787740055",
        "project": TECH_PROJECT_ID,
    }
    res = requests.get("https://app.asana.com/api/1.0/webhooks", headers=headers, params=params)
    print(res.status_code)
    pprint(res.json())


def get_webhook() -> None:
    params: dict[str, str] = {
    }
    res = requests.get("https://app.asana.com/api/1.0/webhooks/1210856413087778", headers=headers, params=params)
    print(res.status_code)
    pprint(res.json())

print(123)
