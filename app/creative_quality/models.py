from asana.models import AtlasUser
from django.db import models, transaction
from django.urls import reverse


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    DELETED = "deleted", "Удален"
    CREATED = "created", "Создан"
    ERROR_LOAD_INFO = "error_load_info", "Ошибка загрузки"


class Task(models.Model):
    task_id = models.CharField(max_length=20, unique=True)
    is_completed = models.BooleanField(default=False)
    task_name = models.CharField(max_length=254, blank=True)
    status = models.CharField(max_length=30, choices=TaskStatus, default=TaskStatus.PENDING)
    assignee_id = models.CharField(max_length=20, blank=True)
    bayer_code = models.CharField(max_length=20, blank=True)
    url = models.CharField(max_length=254, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_assignee_display(self) -> str:
        value = self.assignee_id
        try:
            name = AtlasUser.objects.get(user_id=self.assignee_id).name
            if name:
                value = name
        except AtlasUser.DoesNotExist:
            pass
        return value

    def mark_deleted(self) -> None:
        with transaction.atomic():
            self.status = TaskStatus.DELETED
            self.save()
            if hasattr(self, "creative"):
                self.creative.cancel_estimation()


class CreativeStatus(models.TextChoices):
    WAITING = "waiting", "Ожидает"
    NEED_REVIEW = "need_review", "Нужна оценка"
    RATED = "rated", "Оценено"
    CANCELED = "canceled", "Оценка отменена"
    EXPIRED = "expired", "Просрочено"


class Creative(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="creative")
    status = models.CharField(max_length=50, choices=CreativeStatus, default=CreativeStatus.WAITING)
    comment = models.TextField(blank=True)
    hook = models.PositiveIntegerField(null=True, default=None, blank=True)
    hold = models.PositiveIntegerField(null=True, default=None, blank=True)
    crt = models.PositiveIntegerField(null=True, default=None, blank=True)
    need_rated_at = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    def cancel_estimation(self) -> None:
        self.status = CreativeStatus.CANCELED
        self.need_rated_at = None
        self.save()

    def is_can_be_updated(self) -> bool:
        return True

    def get_estimate_url(self, domain: str | None = None) -> str:
        url = reverse(
            "creative_quality:update-creative",
            kwargs={"creative_id": self.pk, "task_id": self.task.task_id},
        )
        if domain:
            return f"https://{domain}{url}"
        return url


class CreativeProjectSection(models.Model):
    section_id = models.CharField(max_length=30)
    section_name = models.CharField(max_length=254, blank=True)
    project_name = models.CharField(max_length=254, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.section_name if self.section_name else self.section_id
