from django.db import models


class AsanaWebhookProject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    secret = models.CharField(max_length=100, blank=True)


class AsanaWebhookRequestData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(to=AsanaWebhookProject, on_delete=models.CASCADE)
    headers = models.JSONField()
    payload = models.JSONField()
    is_target_event = models.BooleanField(null=True, default=None)


    @property
    def events(self) -> list[dict]:
        return self.payload["events"]


class AsanaComment(models.Model):
    user_id = models.IntegerField()
    task_id = models.IntegerField()
    comment_id = models.IntegerField(unique=True)
    task_url = models.URLField(blank=True)
    has_mention = models.BooleanField(null=True, default=None, blank=True)
    is_notified = models.BooleanField(null=True, blank=True, default=None)
    is_deleted = models.BooleanField(blank=True, default=False)
    text = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def mark_as_deleted(self) -> None:
        self.is_deleted = True
        self.save()


