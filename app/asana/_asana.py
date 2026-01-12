# ruff: noqa
import json
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


def create_webhook():
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


def get_webhooks():
    params = {
        "workspace": 1167322787740055,
        "project": TECH_PROJECT_ID,
    }
    res = requests.get("https://app.asana.com/api/1.0/webhooks", headers=headers, params=params)
    print(res.status_code)
    pprint(res.json())
    # {'data': [{'active': True,
    #            'gid': '1210756910016164',
    #            'resource': {'gid': '1210393628043121',
    #                         'name': 'TECH DEP | Козак Владислав',
    #                         'resource_type': 'project'},
    #            'resource_type': 'webhook',
    #            'target': 'https://atl-asana.vim-store.ru/asana/webhook/'}]}


def get_webhook():
    params = {
        # "workspace": 1167322787740055,
        # "project": PROJECT_ID,
    }
    res = requests.get("https://app.asana.com/api/1.0/webhooks/1210856413087778", headers=headers, params=params)
    print(res.status_code)
    pprint(res.json())


def delete_webhook(webhook_id):
    res = requests.delete(f"https://app.asana.com/api/1.0/webhooks/{webhook_id}", headers=headers)
    print(res.status_code)
    pprint(res.json())


def get_tasks():
    url = "https://app.asana.com/api/1.0/tasks"
    params = {
        "project": "1202274282527282",
        "limit": 10,
    }
    res = requests.get(url, headers=headers, params=params)
    print(res.status_code)
    pprint(res.json())
    if res.status_code == 200:
        with open("tasks.json", "w") as file:
            data = res.json()
            json.dump(data, file, indent=4)


def get_task():
    url = "https://app.asana.com/api/1.0/tasks/1210751306676744"
    params = {
        # "project": "1202274282527282",
        # "limit": 10,
    }
    res = requests.get(url, headers=headers, params=params)
    print(res.status_code)
    pprint(res.json())
    if res.status_code == 200:
        with open("task.json", "w") as file:
            data = res.json()
            json.dump(data, file, indent=4)


def get_sections(project_id):
    url = f"https://app.asana.com/api/1.0/projects/{project_id}/sections"
    res = requests.get(url, headers=headers)
    print(res.status_code)
    pprint(res.json())


    # {
    #     "data": [
    #         {"gid": "1210393628043122", "name": "Общий пул работ, подготовка", "resource_type": "section"},
    #         {"gid": "1210393628043123", "name": "To Do", "resource_type": "section"},
    #         {"gid": "1210393628043134", "name": "In Progress", "resource_type": "section"},
    #         {"gid": "1210393628043135", "name": "На проверке", "resource_type": "section"},
    #         {"gid": "1210393628043136", "name": "Complete", "resource_type": "section"},
    #         {"gid": "1210393561976529", "name": "Быстрые ссылки", "resource_type": "section"},
    #     ]
    # }


def change_webhook():
    url = "https://app.asana.com/api/1.0/webhooks/1210856413087778"
    data = {
        "data": {
            "filters": [
                {"action": "added", "resource_type": "task"},
            ],
        },
    }
    res = requests.put(url, headers=headers, json=data)
    print(res.status_code)
    pprint(res.json())
    if res.status_code == 200:
        with open("task.json", "w") as file:
            data = res.json()
            json.dump(data, file, indent=4)

def get_task(task_id: int):
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    res = requests.get(url, headers=headers,)
    print(res.status_code)
    pprint(res.json())



def send_post_to_table():
    url = "https://script.google.com/macros/s/AKfycbw0D7XfahlxDXgetBhI24hicCvL839QVBD817JEu20LIgqKB71OpCbWUc6jSyCNzhopCg/exec"
    data = {
        "url": "add_new_asana_task",
        "data": {"task_id": "1210844457097784"},
    }
    res = requests.post(url, json=data)
    print(res.status_code)
    try:
        pprint(res.json())
    except:
        print(res.text)

def get_story(story_id: int):
    url = f"https://app.asana.com/api/1.0/stories/{story_id}"
    res = requests.get(url, headers=headers)
    print(res.status_code)
    print(res.text)


def get_workspace_users(workspace: int):
    url = f"https://app.asana.com/api/1.0/workspaces/{workspace}/users"
    res = requests.get(url, headers=headers)
    print(res.status_code)
    print(res.text)

def get_workspace(workspace: int):
    url = f"https://app.asana.com/api/1.0/workspaces/{workspace}"
    res = requests.get(url, headers=headers)
    print(res.status_code)
    print(res.text)

def get_user(user: int):
    url = f"https://app.asana.com/api/1.0/users/{user}"
    params={
        "opt_fields": ["photo"],
    }
    res = requests.get(url, headers=headers)
    print(res.status_code)
    pprint(res.json())


# def test(workspace_membership_gid):
#     url = f"https://app.asana.com/api/1.0/workspace_memberships/{workspace_membership_gid}"
#     res = requests.get(url, headers=headers)
#     print(res.status_code)
#     pprint(res.json())


def get_task_from_section(section_gid):
    url = f"https://app.asana.com/api/1.0/sections/{section_gid}/tasks"
    res = requests.get(url, headers=headers)
    print(res.status_code)
    res = res.json()
    pprint(res)
    print(len(res["data"]))


# create_webhook()
# create_webhook()
print(123)