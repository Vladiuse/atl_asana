from datetime import date

import pytest
from message_sender.models import AtlasUser

from leave_events.models import Leave, LeaveType, SupervisorNotificationChat


@pytest.fixture
def leave_vacation() -> Leave:
    return Leave.objects.create(
        employee="xxx",
        supervisor_tag="@xxx",
        start_date=date(2000, 1, 1),
        end_date=date(2000, 1, 1),
        type=LeaveType.VACATION,
    )


@pytest.fixture
def leave_day_off() -> Leave:
    return Leave.objects.create(
        employee="xxx",
        supervisor_tag="@xxx",
        start_date=date(2000, 2, 2),
        end_date=date(2000, 2, 2),
        type=LeaveType.DAY_OFF,
    )


@pytest.fixture
def atlas_user() -> AtlasUser:
    return AtlasUser.objects.create(
        name="Test User",
        email="test@example.com",
        role="tester",
        tag="test_tag",
        telegram="test_telegram_login",
        username="test_username",
    )


@pytest.fixture
def supervisor_chat(atlas_user: AtlasUser) -> SupervisorNotificationChat:
    return SupervisorNotificationChat.objects.create(supervisor=atlas_user, chat="CHAT")
