import pytest
from message_sender.models import AtlasUser
from rest_framework.exceptions import ValidationError

from leave_events.serializers import LeaveSerializer


@pytest.fixture(autouse=True)
def atlas_user() -> AtlasUser:
    return AtlasUser.objects.create(
        name="Test User",
        email="test@example.com",
        role="tester",
        tag="test_tag",
        telegram="test_telegram_login",
        username="test_username",
    )


@pytest.mark.django_db
def test_validate_telegram_login() -> None:
    serializer = LeaveSerializer()
    assert serializer.validate_telegram_login("test_telegram_login") == "test_telegram_login"
    assert serializer.validate_telegram_login("@test_telegram_login") == "test_telegram_login"
    with pytest.raises(ValidationError) as exc_info:
        serializer.validate_telegram_login("wrong_telegram")
    assert "telegram_login" in exc_info.value.detail
