from django.db import models


class AsanaWebhookProject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    project_id = models.CharField(max_length=50, unique=True)
    project_name = models.CharField(max_length=254, blank=True)
    project_url = models.URLField(blank=True)
    secret = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.project_name if self.project_name else self.name

class ProjectTargetSection(models.Model):
    project = models.ForeignKey(to=AsanaWebhookProject, on_delete=models.CASCADE, unique=True)
    section_id = models.CharField(max_length=20, unique=True)
    section_name = models.CharField(max_length=254, blank=True)


class AsanaWebhookRequestData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(to=AsanaWebhookProject, on_delete=models.CASCADE)
    headers = models.JSONField()
    payload = models.JSONField()
    is_target_event = models.BooleanField(null=True, default=None)

    @property
    def events(self) -> list[dict]:
        return self.payload["events"]


class Task(models.Model):
    project = models.ForeignKey(to=AsanaWebhookProject, on_delete=models.CASCADE, unique=True)
    task_id = models.CharField(max_length=20, unique=True)
    task_name = models.CharField(max_length=254, blank=True)
    is_complete  = models.BooleanField(default=False)
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