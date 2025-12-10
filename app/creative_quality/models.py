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


class Creative(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="creative")
    is_rated = models.BooleanField(default=False)
    hook = models.PositiveIntegerField(null=True, default=None, blank=True)
    hold = models.PositiveIntegerField(null=True, default=None, blank=True)
    crt = models.PositiveIntegerField(null=True, default=None, blank=True)
    need_rated_at = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
