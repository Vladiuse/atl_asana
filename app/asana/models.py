from common.message_sender import Users
from django.core.exceptions import ValidationError
from django.db import models

from .constants import Position
from .utils import get_asana_profile_url_by_id


class AtlasUser(models.Model):
    user_id = models.PositiveIntegerField(unique=True)
    membership_id = models.PositiveIntegerField(unique=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=254)
    avatar_url = models.URLField(blank=True)
    messenger_code = models.CharField(
        max_length=32,
        choices=Users.choices(),
        blank=True,
    )
    position = models.CharField(
        blank=True,
        max_length=32,
        choices=Position.choices,
        verbose_name="Позиция",
    )

    @property
    def user_comment_mention(self) -> str:
        return "@" + self.name

    @property
    def profile_url(self) -> str:
        return get_asana_profile_url_by_id(profile_id=self.membership_id)

    def clean(self) -> None:
        super().clean()
        if bool(self.messenger_code) != bool(self.position):
            raise ValidationError("Оба поля messenger_code и position должны быть либо заполнены, либо пусты.")
