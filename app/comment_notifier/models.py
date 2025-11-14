from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet


class AsanaWebhookProject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    project_id = models.CharField(max_length=50, unique=True)
    project_name = models.CharField(max_length=254, blank=True)
    project_url = models.URLField(blank=True)
    secret = models.CharField(max_length=100, blank=True)

    if TYPE_CHECKING:
        ignored_sections: "QuerySet[ProjectIgnoredSection]"

    def __str__(self):
        return self.project_name if self.project_name else self.name


class ProjectIgnoredSection(models.Model):
    project = models.ForeignKey(
        to=AsanaWebhookProject,
        on_delete=models.CASCADE,
        related_name="ignored_sections",
        related_query_name="ignored_section",
    )
    section_id = models.CharField(max_length=30)
    section_name = models.CharField(max_length=254, blank=True)

    class Meta:
        unique_together = ["project", "section_id"]

    def __str__(self):
        return self.section_name if self.section_name else f"{self.project}:{self.section_id}"


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
    project = models.ForeignKey(
        to=AsanaWebhookProject,
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL,
    )
    has_mention = models.BooleanField(null=True, default=None, blank=True)
    is_notified = models.BooleanField(null=True, blank=True, default=None)
    is_deleted = models.BooleanField(blank=True, default=False)
    text = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def mark_as_deleted(self) -> None:
        self.is_deleted = True
        self.save()
