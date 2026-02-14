from datetime import date

import pytest

from leave_events.models import Leave, LeaveType


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
