from django.db import models


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
