from django.db import models


class OffboardingTask(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        COMPLETED = "completed", "Завершена"
        DELETED = "deleted", "Удалена"
        ERROR = "error", "Ошибка"

    asana_task_id = models.CharField(
        max_length=30,
    )
    is_complete = models.BooleanField(
        default=False,
    )
    notified_created_at = models.DateTimeField()
    notified_created = models.BooleanField(default=False)
    notified_need_payroll = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return f"<OffboardingTask:{self.asana_task_id}"
