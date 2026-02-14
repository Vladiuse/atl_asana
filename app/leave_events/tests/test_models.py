from datetime import date

import pytest
from django.utils import timezone
from message_sender.models import ScheduledMessage

from leave_events.models import Leave, LeaveType


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


@pytest.mark.django_db
class TestMessages:
    def test_no_messages(self, leave_vacation: Leave, leave_day_off: Leave) -> None:
        empty_leave = Leave.objects.create(
            employee="xxx",
            supervisor_tag="@xxx",
            start_date=date(2000, 3, 3),
            end_date=date(2000, 1, 1),
            type=LeaveType.VACATION,
        )
        message_1 = ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave_vacation.pk}",
        )
        message_2 = ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave_day_off.pk}",
        )
        message_3 = ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave_day_off.pk}",
        )
        assert empty_leave.messages.count() == 0
        assert leave_vacation.messages.count() == 1
        assert leave_day_off.messages.count() == 2
        assert message_1 in leave_vacation.messages
        assert message_2 in leave_day_off.messages
        assert message_3 in leave_day_off.messages
