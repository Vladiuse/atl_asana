from datetime import date

import pytest
from django.utils import timezone
from message_sender.models import ScheduledMessage

from leave_events.models import Leave, LeaveStatus, LeaveType


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


@pytest.mark.django_db
class TestLeaveDeleteModel:
    def test_no_messages(self, leave_vacation: Leave) -> None:
        """Check that no raises if execute .delete() method."""
        leave_vacation.delete()

    def test_have_few_messages(self, leave_vacation: Leave) -> None:
        ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave_vacation.pk}",
        )
        leave_vacation.delete()
        assert ScheduledMessage.objects.count() == 0

    def test_delete_by_reference(self, leave_vacation: Leave, leave_day_off: Leave) -> None:
        ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave_vacation.pk}",
        )
        ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave_day_off.pk}",
        )
        leave_vacation.delete()
        assert ScheduledMessage.objects.filter(reference_id=f"leave-{leave_day_off.pk}").count() == 1
