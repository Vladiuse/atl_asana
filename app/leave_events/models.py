from datetime import timedelta
from typing import Any

from django.db import models, transaction
from django.utils import timezone
from message_sender.models import ScheduledMessage


class LeaveType(models.TextChoices):
    VACATION = "VACATION", "Отпуск"
    DAY_OFF = "DAY_OFF", "Отгул"


class LeaveNotificationManager(models.Manager):  # type: ignore[type-arg]
    def create(self, **kwargs: Any) -> "LeaveNotification":  # noqa: ANN401
        with transaction.atomic():
            leave = super().create(**kwargs)
            ScheduledMessage.objects.create(
                run_at=timezone.now() + timedelta(minutes=5),
                text=f"Отпуск создан: {leave.start_date} – {leave.end_date}",
                user_tag="kva_tech",
                reference_id=f"leave-{leave.pk}",
            )
            ScheduledMessage.objects.create(
                run_at=leave.start_date - timedelta(weeks=2),
                text=f"Напоминание: отпуск с {leave.start_date} по {leave.end_date}",
                user_tag="kva_tech",
                reference_id=f"leave-{leave.pk}",
            )
            return leave


class LeaveNotification(models.Model):
    type = models.CharField(max_length=30, choices=LeaveType)
    employee = models.CharField(max_length=254)
    supervisor_tag = models.CharField(max_length=254)
    start_date = models.DateField()
    end_date = models.DateField()
    cancellable_until = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)

    objects = LeaveNotificationManager()

    class Meta:
        unique_together = ("employee", "start_date")

    def __str__(self) -> str:
        return f"{self.employee}:{self.start_date}"

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        ScheduledMessage.objects.filter(reference_id=f"leave-{self.pk}").delete()
        return super().delete(*args, **kwargs)

    def is_can_be_deleted(self) -> bool:
        return self.cancellable_until > timezone.now()
