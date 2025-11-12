from django.db import models


class Webhook(models.Model):
    webhook_id = models.CharField(unique=True)
    resource_name = models.CharField(max_length=100, blank=True)
    resource_type = models.CharField(max_length=100, blank=True)
    target = models.URLField(blank=True)
    description = models.CharField(max_length=254, blank=True)
