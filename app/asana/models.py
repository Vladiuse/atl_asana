from django.db import models


class AtlasUser(models.Model):
    user_id = models.PositiveIntegerField(unique=True)
    atlas_profile_id = models.PositiveIntegerField(unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=254)
    avatar_url = models.URLField(blank=True)
