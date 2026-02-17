from typing import Any

from django.db import models
from django.db.models import QuerySet
from message_sender.models import ScheduledMessage


class LeaveType(models.TextChoices):
    VACATION = "VACATION", "Отпуск"
    DAY_OFF = "DAY_OFF", "Отгул"


class LeaveStatus(models.TextChoices):
    PENDING = "pending", "Нужно согласовать"
    APPROVED = "approved", "Согласовано"
    DELETED = "deleted", "Удалено"


class LeaveQuerySet(models.QuerySet["Leave"]):
    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        _ = args, kwargs
        count = 0
        for obj in self:
            obj.delete()
            count += 1
        return count, {}


class LeaveManager(models.Manager.from_queryset(LeaveQuerySet)):  # type: ignore[misc]
    pass


class Leave(models.Model):
    type = models.CharField(
        max_length=30,
        choices=LeaveType,
    )
    employee = models.CharField(
        max_length=254,
    )
    telegram_login = models.CharField(
        max_length=254,
    )
    supervisor_tag = models.CharField(
        max_length=254,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=30,
        choices=LeaveStatus.choices,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    objects = LeaveManager()

    class Meta:
        unique_together = ("employee", "start_date")

    def __str__(self) -> str:
        return f"{self.employee}:{self.start_date}"

    @property
    def messages(self) -> QuerySet[ScheduledMessage]:
        return ScheduledMessage.objects.filter(reference_id=f"leave-{self.pk}")

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        ScheduledMessage.objects.filter(reference_id=f"leave-{self.pk}").delete()
        return super().delete(*args, **kwargs)
