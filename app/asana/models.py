from django.db import models


class AsanaWebhookRequestData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    headers = models.JSONField()
    payload = models.JSONField()
