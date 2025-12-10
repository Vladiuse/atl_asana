from django.db import models

class TaskStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    DELETED = "deleted", "Удален"
    CREATED = "created", "Создан"
    ERROR_LOAD_INFO = "error_load_info", "Ошибка загрузки"


class Task(models.Model):
    task_id = models.CharField(max_length=20, unique=True)
    task_name = models.CharField(max_length=254, blank=True)
    is_complete = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=TaskStatus, default=TaskStatus.PENDING)
    assignee_id = models.CharField(max_length=20, blank=True)
    bayer_code = models.CharField(max_length=20, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class CreativeStatus(models.TextChoices):
    WAITING = "waiting", "Ожидает оценки"
    RATED = "rated", "Оценено"
    CANCELED = "canceled", "Оценка отменена"
    EXPIRED = "expired", "Просрочено"


class Creative(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="creative")
    status = models.CharField(max_length=50, choices=CreativeStatus, default=CreativeStatus.WAITING)
    hook = models.PositiveIntegerField(null=True, default=None, blank=True)
    hold = models.PositiveIntegerField(null=True, default=None, blank=True)
    crt = models.PositiveIntegerField(null=True, default=None, blank=True)
    need_rated_at = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)


class CreativeProjectSection(models.Model):
    section_id = models.CharField(max_length=30)
    section_name = models.CharField(max_length=254, blank=True)
    project_name = models.CharField(max_length=254, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.section_name if self.section_name else self.section_id
