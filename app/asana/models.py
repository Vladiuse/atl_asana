from common.message_sender import UserTag
from django.db import models

from .constants import Position
from .utils import get_asana_profile_url_by_id


class AtlasUser(models.Model):
    user_id = models.CharField(unique=True)
    membership_id = models.CharField(unique=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=254)
    avatar_url = models.URLField(blank=True, max_length=254)
    messenger_code = models.CharField(
        max_length=32,
        choices=UserTag.choices(),
        blank=True,
        null=True,
        default=None,
    )
    position = models.CharField(
        blank=True,
        max_length=32,
        choices=Position.choices,
        verbose_name="Позиция",
    )

    def __str__(self):
        return self.name if self.name else self.email

    @property
    def user_comment_mention(self) -> str:
        return "@" + self.name

    @property
    def profile_url(self) -> str:
        return get_asana_profile_url_by_id(profile_id=self.membership_id)


class AsanaResourceType(models.TextChoices):
    PROJECT = "project", "Проект"
    SECTION = "section", "Секция"


class AsanaWebhook(models.Model):
    name = models.CharField(max_length=100, unique=True)
    resource_id = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50, choices=AsanaResourceType.choices)
    resource_name = models.CharField(max_length=254, blank=True)
    secret = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    handlers = models.ManyToManyField(to="WebhookHandler", related_name="webhooks")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resource_type}:{self.resource_name}" if self.resource_name else self.name


class AsanaWebhookRequestData(models.Model):
    webhook = models.ForeignKey(to=AsanaWebhook, on_delete=models.CASCADE)
    headers = models.JSONField()
    payload = models.JSONField()
    is_target_event = models.BooleanField(null=True, default=None)
    additional_data = models.JSONField(blank=True, default=dict)
    created = models.DateTimeField(auto_now_add=True)

    @property
    def events(self) -> list[dict]:
        return self.payload["events"]


class WebhookHandler(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)