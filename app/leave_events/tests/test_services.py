from datetime import date

import pytest
from django.utils import timezone
from message_sender.models import ScheduledMessage

from leave_events.models import Leave, LeaveStatus, LeaveType
from leave_events.services import LeaveNotificationService


@pytest.fixture
def service() -> LeaveNotificationService:
    return LeaveNotificationService()


@pytest.mark.django_db
class TestLeaveServicePending:
    def test_no_exist_in_db(self, service: LeaveNotificationService) -> None:
        """Leave no exist in db/ must be created."""
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
        }
        leave = service._need_agreed(leave_data=leave_data)
        assert Leave.objects.count() == 1
        assert ScheduledMessage.objects.filter(reference_id=f"leave-{leave.pk}").count() == 1

    def test_exist_in_db(self, service: LeaveNotificationService) -> None:
        """Leave already exist in db. Must be removed old messages."""
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.APPROVED.value,
        }
        leave_orig = Leave.objects.create(**leave_data)
        for _ in range(2):
            ScheduledMessage.objects.create(
                text="x",
                user_tag="x",
                run_at=timezone.now(),
                reference_id=f"leave-{leave_orig.pk}",
            )
        assert leave_orig.messages.count() == 2
        assert leave_orig.status == LeaveStatus.APPROVED.value
        leave_data["status"] = LeaveStatus.PENDING.value
        leave = service._need_agreed(leave_data=leave_data)
        assert Leave.objects.count() == 1
        assert ScheduledMessage.objects.filter(reference_id=f"leave-{leave.pk}").count() == 1
        assert leave_orig.pk == leave.pk
        assert leave.status == LeaveStatus.PENDING.value
        assert leave.messages.count() == 1
