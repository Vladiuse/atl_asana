from django.core.exceptions import ValidationError
from django.db import models

from message_sender.client import Handlers


class AtlasUser(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=64)
    tag = models.CharField(max_length=64, null=True, unique=True, blank=True)
    telegram = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        if self.tag:
            return f"{self.name} ({self.tag})"
        return self.name


class ScheduledMessageStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class ScheduledMessage(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"

    status = models.CharField(
        max_length=20,
        choices=ScheduledMessageStatus,
        default=STATUS_PENDING,
    )
    run_at = models.DateTimeField()
    user_tag = models.CharField(
        max_length=30,
        blank=True,
    )
    handler = models.CharField(
        max_length=30,
        blank=True,
        choices=[(tag.value, tag.name) for tag in Handlers],
    )
    text = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = (models.Index(fields=["status", "run_at"]),)

    def __str__(self) -> str:
        return f"{self.status} @ {self.run_at}"

    def clean(self) -> None:
        filled_fields = [bool(self.user_tag), bool(self.handler)]
        if sum(filled_fields) != 1:
            raise ValidationError("Only one of the fields 'user_tag' or 'handler' must be filled.")
