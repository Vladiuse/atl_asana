from django.db import models


class AsanaProject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    secret = models.CharField(max_length=100, blank=True)


class AsanaWebhookRequestData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(to=AsanaProject, on_delete=models.CASCADE)
    headers = models.JSONField()
    payload = models.JSONField()
    is_target_event = models.BooleanField(null=True, default=None)


    @property
    def events(self) -> list[dict]:
        return self.payload["events"]
