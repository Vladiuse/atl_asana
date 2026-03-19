from asana.constants import AtlasProject

RESOURCE_ID = "1234567890987654321"
CREATE_TASK_EVENT_CORRECT_PROJECT = {
    "events": [
        {
            "user": {"gid": "1213537811762722", "resource_type": "user"},
            "action": "added",
            "parent": {"gid": AtlasProject.OFFBOARDING.value, "resource_type": "project"},
            "resource": {"gid": RESOURCE_ID, "resource_type": "task", "resource_subtype": "default_task"},
            "created_at": "2026-03-17T10:11:06.474Z",
        },
        {
            "user": {"gid": "1213537811762722", "resource_type": "user"},
            "action": "added",
            "parent": {"gid": "1211316915894850", "resource_type": "section"},
            "resource": {"gid": RESOURCE_ID, "resource_type": "task", "resource_subtype": "default_task"},
            "created_at": "2026-03-17T10:11:06.611Z",
        },
    ],
}

CREATE_TASK_EVENT = {
    "events": [
        {
            "user": {"gid": "1213537811762722", "resource_type": "user"},
            "action": "added",
            "parent": {"gid": "123123123", "resource_type": "project"},
            "resource": {"gid": RESOURCE_ID, "resource_type": "task", "resource_subtype": "default_task"},
            "created_at": "2026-03-17T10:11:06.474Z",
        },
        {
            "user": {"gid": "1213537811762722", "resource_type": "user"},
            "action": "added",
            "parent": {"gid": "1211316915894850", "resource_type": "section"},
            "resource": {"gid": RESOURCE_ID, "resource_type": "task", "resource_subtype": "default_task"},
            "created_at": "2026-03-17T10:11:06.611Z",
        },
    ],
}


CREATE_SUB_TASK_EVENT = {
    "events": [
        {
            "user": {"gid": "1213537811762722", "resource_type": "user"},
            "action": "added",
            "parent": {"gid": "1213717492740873", "resource_type": "task", "resource_subtype": "default_task"},
            "resource": {"gid": RESOURCE_ID, "resource_type": "task", "resource_subtype": "default_task"},
            "created_at": "2026-03-17T10:11:18.514Z",
        },
    ],
}
