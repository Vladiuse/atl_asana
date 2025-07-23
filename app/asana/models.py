from django.db import models


class AsanaProject(models.Model):
    name = models.CharField(max_length=100)
    complete_section_id = models.CharField(max_length=100)
    table_url = models.CharField(max_length=100, unique=True)
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

class CompletedTask(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    project = models.OneToOneField(to=AsanaProject, on_delete=models.CASCADE)
    webhook = models.ForeignKey(to=AsanaWebhookRequestData, on_delete=models.CASCADE)
    event_data = models.JSONField()
    task_id = models.CharField(max_length=100)
    is_send_in_table = models.BooleanField(null=True, default=None)
    response_text = models.TextField(blank=True)
    error_text = models.TextField(blank=True)
