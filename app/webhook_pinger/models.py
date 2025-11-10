from django.db import models


class Webhook(models.Model):
    webhook_id = models.IntegerField(unique=True)
    description = models.CharField(max_length=254, blank=True)
