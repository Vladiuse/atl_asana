from datetime import date, timedelta

import pytest
from django.utils import timezone
from message_sender.models import AtlasUser, ScheduledMessage

from leave_events.models import Leave, LeaveStatus, LeaveType, SupervisorNotificationChat
from leave_events.services import LeaveNotificationService


@pytest.fixture
def service() -> LeaveNotificationService:
    return LeaveNotificationService()


USER_TAG = "TAG"


@pytest.fixture
def atlas_user() -> AtlasUser:
    return AtlasUser.objects.create(
        name="Test User",
        email="test@example.com",
        role="tester",
        tag=USER_TAG,
        telegram="test_telegram_login",
        username="test_username",
    )


@pytest.mark.django_db
class TestLeaveServicePending:
    def test_no_exist_in_db(
        self, service: LeaveNotificationService, supervisor_chat: SupervisorNotificationChat,
    ) -> None:
        """Leave no exist in db/ must be created."""
        _ = supervisor_chat
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "test_telegram_login",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": "test_telegram_login",
        }
        leave = service._need_agreed(leave_data=leave_data)
        assert Leave.objects.count() == 1
        assert ScheduledMessage.objects.filter(reference_id=f"leave-{leave.pk}").count() == 1

    def test_exist_in_db(self, service: LeaveNotificationService, atlas_user: AtlasUser) -> None:
        """Leave already exist in db. Must be removed old messages."""
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.APPROVED.value,
            "telegram_login": "@" + atlas_user.telegram,
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
        assert leave.messages.filter(handler=service.handler).count() == 1


@pytest.mark.django_db
class TestApproved:
    def test_no_exist_in_db(self, service: LeaveNotificationService, atlas_user: AtlasUser) -> None:
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": atlas_user.telegram,
        }
        with pytest.raises(Leave.DoesNotExist):
            service._approved(leave_data=leave_data)

    def test_no_employee(self, service: LeaveNotificationService, atlas_user: AtlasUser) -> None:
        """No user with the specified telegram login in the database."""
        _ = atlas_user
        Leave.objects.create(
            employee="xxx",
            supervisor_tag="xxx",
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 1),
            type=LeaveType.DAY_OFF,
            status=LeaveStatus.PENDING,
            telegram_login="some",
        )
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.APPROVED.value,
            "telegram_login": "some",
        }
        with pytest.raises(AtlasUser.DoesNotExist):
            service._approved(leave_data=leave_data)

    def test_exist_in_db(self, service: LeaveNotificationService, atlas_user: AtlasUser) -> None:
        start_date = date(3000, 1, 1)
        leave = Leave.objects.create(
            employee="xxx",
            supervisor_tag="xxx",
            start_date=start_date,
            end_date=date(2000, 1, 1),
            type=LeaveType.DAY_OFF,
            status=LeaveStatus.PENDING,
            telegram_login=atlas_user.telegram,
        )
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": start_date,
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": atlas_user.telegram,
        }
        leave = service._approved(leave_data=leave_data)
        assert leave.status == LeaveStatus.APPROVED
        assert leave.messages.count() == 2
        assert leave.messages.filter(user_tag=USER_TAG).count() == 1
        assert leave.messages.filter(handler=service.handler).count() == 1

    @pytest.mark.parametrize(
        ("days_delta", "message_count"),
        [
            (14, 2),
            (7, 2),
            (5, 1),
        ],
    )
    def test_create_reminder(
        self,
        service: LeaveNotificationService,
        days_delta: int,
        message_count: int,
        atlas_user: AtlasUser,
    ) -> None:
        start_date = timezone.now().date() + timedelta(days=days_delta)
        leave = Leave.objects.create(
            employee="xxx",
            supervisor_tag="xxx",
            start_date=start_date,
            end_date=date(2000, 1, 1),
            type=LeaveType.DAY_OFF,
            status=LeaveStatus.PENDING,
            telegram_login=atlas_user.telegram,
        )
        first_message = ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave.pk}",
        )
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": start_date,
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": atlas_user.telegram,
        }
        leave = service._approved(leave_data=leave_data)
        assert leave.status == LeaveStatus.APPROVED
        assert leave.messages.exclude(pk=first_message.pk).count() == message_count


@pytest.mark.django_db
class TestDelete:
    def test_not_exist_in_db(self, service: LeaveNotificationService) -> None:
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
        }
        with pytest.raises(Leave.DoesNotExist):
            service._delete(leave_data=leave_data)

    def test_exist_in_db(self, service: LeaveNotificationService) -> None:
        leave = Leave.objects.create(
            employee="xxx",
            supervisor_tag="xxx",
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 1),
            type=LeaveType.DAY_OFF,
            status=LeaveStatus.PENDING,
        )
        ScheduledMessage.objects.create(
            text="x",
            user_tag="x",
            run_at=timezone.now(),
            reference_id=f"leave-{leave.pk}",
        )
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "xxx",
            "start_date": date(2000, 1, 1),
            "end_date": date(2000, 1, 1),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
        }
        service._delete(leave_data=leave_data)
        assert Leave.objects.count() == 0
        assert leave.messages.count() == 0
