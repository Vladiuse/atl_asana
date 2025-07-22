from django.db import models


class AsanaWebhookRequestData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    headers = models.JSONField()
    payload = models.JSONField()
    is_target_event = models.BooleanField(default=False)


    @property
    def events(self) -> list[dict]:
        return self.payload["events"]

class CompletedTask(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    webhook = models.ForeignKey(to=AsanaWebhookRequestData, on_delete=models.CASCADE)
    event_data = models.JSONField()
    task_id = models.CharField(max_length=100)
