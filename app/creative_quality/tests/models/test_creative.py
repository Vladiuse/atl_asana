from datetime import datetime
from unittest.mock import Mock

import pytest
from django.utils import timezone

from creative_quality.models import Creative, CreativeStatus, Task


@pytest.fixture()
def fixed_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    fixed = timezone.make_aware(datetime(2025, 1, 1, 12, 0, 0))
    monkeypatch.setattr(timezone, "now", lambda: fixed)
    return fixed

@pytest.fixture()
def creative_model() -> Creative:
    task = Task.objects.create(task_id="x")
    return  Creative.objects.create(task=task, status=CreativeStatus.WAITING)


@pytest.mark.django_db()
class TestCreative:
    @pytest.mark.parametrize(
        ("method_name", "status", "next_reminder_at"),
        [
            ("mark_rated", CreativeStatus.RATED, None),
            ("mark_need_estimate", CreativeStatus.NEED_ESTIMATE, timezone.now()),
            ("mark_reminder_limit_reached", CreativeStatus.REMINDER_LIMIT_REACHED, None),
            ("cancel_estimation", CreativeStatus.CANCELED, None),
        ],
    )
    def test_mark(
        self,
        method_name: str,
        status: CreativeStatus,
        next_reminder_at: datetime | None,
        fixed_now: datetime,
        creative_model: Creative,
    ):

        method = getattr(creative_model, method_name)
        method()
        creative_model.reminder_at = next_reminder_at
        assert creative_model.status == status
        if next_reminder_at is not None:
            assert creative_model.next_reminder_at == fixed_now
        else:
            assert creative_model.next_reminder_at is None

    @pytest.mark.parametrize("save", [True, False])
    @pytest.mark.parametrize(
        "method_name", ["mark_rated", "mark_need_estimate", "mark_reminder_limit_reached", "cancel_estimation"],
    )
    def test_mark_save(self, save: bool, method_name: str, creative_model: Creative):
        creative_model.save = Mock()
        method = getattr(creative_model, method_name)
        method(save=save)
        if save:
            assert creative_model.save.called
        else:
            creative_model.save.assert_not_called()

