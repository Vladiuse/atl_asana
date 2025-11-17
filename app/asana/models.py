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
