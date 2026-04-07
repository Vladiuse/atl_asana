import pytest
from rest_framework.exceptions import ValidationError

from leave_events.models import LeaveStatus, SupervisorNotificationChat
from leave_events.serializers import LeaveSerializer


@pytest.mark.django_db
class TestLeaveSerializer:
    def test_to_internal_value(self, supervisor_chat: SupervisorNotificationChat) -> None:
        _ = supervisor_chat
        data = {
            "telegram_login": "@test_telegram_login",
            "supervisor_tag": "@test_telegram_login",
            "employee": "Ivan Ivanov",
            "type": "VACATION",
            "start_date": "2026-04-10",
            "end_date": "2026-04-15",
            "status": LeaveStatus.PENDING.value,
        }
        serializer = LeaveSerializer()
        result = serializer.to_internal_value(data)
        assert result["telegram_login"] == "test_telegram_login"
        assert result["supervisor_tag"] == "test_telegram_login"

    def test_unknown_employee_super_visor(self, supervisor_chat: SupervisorNotificationChat) -> None:
        _ = supervisor_chat
        data = {
            "telegram_login": "@xxx",
            "supervisor_tag": "@yyy",
            "employee": "Ivan Ivanov",
            "type": "VACATION",
            "start_date": "2026-04-10",
            "end_date": "2026-04-15",
            "status": LeaveStatus.PENDING.value,
        }
        serializer = LeaveSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert "telegram_login" in serializer.errors
        assert "supervisor_tag" in serializer.errors

    def test_supervisor_chat_not_exist(self, supervisor_chat: SupervisorNotificationChat) -> None:
        supervisor_chat.delete()
        data = {
            "telegram_login": "@test_telegram_login",
            "supervisor_tag": "@test_telegram_login",
            "employee": "Ivan Ivanov",
            "type": "VACATION",
            "start_date": "2026-04-10",
            "end_date": "2026-04-15",
            "status": LeaveStatus.PENDING.value,
        }
        serializer = LeaveSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert "supervisor_tag" in serializer.errors
        assert (
            serializer.errors["supervisor_tag"]["supervisor_tag"]
            == "Supervisor @test_telegram_login dont have chat to notify"
        )
