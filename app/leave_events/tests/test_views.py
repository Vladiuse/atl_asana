from datetime import date

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from message_sender.models import AtlasUser
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from leave_events.models import Leave, LeaveStatus, LeaveType, SupervisorNotificationChat
from leave_events.services import LeaveNotificationService


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username="test_user", password="password123")  # noqa: S106


@pytest.fixture
def auth_client(user: User) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@pytest.fixture
def service() -> LeaveNotificationService:
    return LeaveNotificationService()


@pytest.mark.django_db
class TestLeaveUpdateByStatusView:
    @property
    def url(self) -> str:
        return reverse("leave_events:leave-notification-process-by-status")

    def test_no_auth(self, api_client: APIClient) -> None:
        response = api_client.post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        ("leave_status", "status_code"),
        [
            (LeaveStatus.DELETED, status.HTTP_404_NOT_FOUND),
            (LeaveStatus.APPROVED, status.HTTP_404_NOT_FOUND),
            (LeaveStatus.PENDING, status.HTTP_200_OK),
        ],
    )
    def test_leave_not_exists(
        self,
        auth_client: APIClient,
        leave_status: LeaveStatus,
        status_code: int,
        supervisor_chat: SupervisorNotificationChat,
    ) -> None:
        _ = supervisor_chat
        leave_data = {
            "employee": "xxx",
            "supervisor_tag": "test_telegram_login",
            "start_date": date(2025, 1, 1).isoformat(),
            "end_date": date(2025, 1, 1).isoformat(),
            "type": LeaveType.DAY_OFF.value,
            "status": leave_status.value,
            "telegram_login": "@test_telegram_login",
        }
        response = auth_client.post(self.url, data=leave_data)
        assert response.status_code == status_code

    def test_employee_not_exist_in_db(self, auth_client: APIClient) -> None:
        AtlasUser.objects.all().delete()
        leave_data = {
            "employee": "test_emp",
            "supervisor_tag": "test_sup",
            "start_date": date(2025, 1, 1).isoformat(),
            "end_date": date(2025, 1, 1).isoformat(),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": "@test_telegram_login",
        }
        response = auth_client.post(self.url, data=leave_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_leave_in_db(self, auth_client: APIClient) -> None:
        leave_data = {
            "employee": "test_emp",
            "supervisor_tag": "test_sup",
            "start_date": date(2025, 1, 1).isoformat(),
            "end_date": date(2025, 1, 1).isoformat(),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": "@test_telegram_login",
        }
        response = auth_client.post(self.url, data=leave_data, format="json")
        assert response.status_code == 200
        leave = Leave.objects.get(employee="test_emp", start_date="2025-01-01")
        assert leave.supervisor_tag == "test_sup"
        assert leave.type == LeaveType.DAY_OFF
        assert leave.status == LeaveStatus.PENDING

    def test_update_and_delete(self, auth_client: APIClient) -> None:
        """Create leave in DB and then try to delete."""
        leave_data = {
            "employee": "test_emp",
            "supervisor_tag": "test_sup",
            "start_date": date(2025, 1, 1).isoformat(),
            "end_date": date(2025, 1, 1).isoformat(),
            "type": LeaveType.DAY_OFF.value,
            "status": LeaveStatus.PENDING.value,
            "telegram_login": "@test_telegram_login",
        }
        response = auth_client.post(self.url, data=leave_data, format="json")
        assert response.status_code == 200
        leave_data["status"] = LeaveStatus.DELETED.value
        response = auth_client.post(self.url, data=leave_data, format="json")
        assert response.status_code == 200
