from django.db import models


class Position(models.TextChoices):
    BUYER = "buyer", "Баер"
    FARMER = "farmer", "Фармер"


class AtlasUser(models.Model):
    user_id = models.PositiveIntegerField(unique=True)
    atlas_profile_id = models.PositiveIntegerField(unique=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=254)
    avatar_url = models.URLField(blank=True)
    position = models.CharField(
        blank=True,
        max_length=32,
        choices=Position.choices,
        verbose_name="Позиция",
    )
