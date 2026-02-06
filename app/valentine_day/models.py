from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Employee(models.Model):
    image = models.ImageField(
        upload_to="valentine_day/images/avatars",
        null=True,
        blank=True,
        max_length=255,
    )
    name = models.CharField(
        max_length=50,
    )
    surname = models.CharField(
        max_length=50,
    )
    position = models.CharField(
        max_length=100,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"


class ValentineImage(models.Model):
    image = models.ImageField(
        upload_to="valentine_day/images/for_valentines",
        null=True,
        blank=True,
        max_length=255,
    )
    owner = models.ForeignKey(
        to=Employee,
        on_delete=models.CASCADE,
        null=True,
        default=None,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return f"<ValentineImage: {self.pk}>"


class Valentine(models.Model):
    sender = models.ForeignKey(
        to=Employee,
        on_delete=models.CASCADE,
        related_name="sent_valentines",
    )
    recipient = models.ForeignKey(
        to=Employee,
        on_delete=models.CASCADE,
        related_name="received_valentines",
    )
    image = models.ForeignKey(
        to=ValentineImage,
        on_delete=models.PROTECT,
    )
    text = models.TextField()
    is_anonymously = models.BooleanField()
    anonymous_signature = models.TextField(
        max_length=50,
        blank=True,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        unique_together = ("sender", "recipient")
        constraints = (
            models.CheckConstraint(
                name="anonymous_requires_signature",
                condition=(Q(is_anonymously=False) | Q(anonymous_signature__gt="")),
            ),
        )

    def __str__(self) -> str:
        return f"{self.sender} to {self.recipient}"

    def save(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        if not self.is_anonymously:
            self.anonymous_signature = ""
        super().save(*args, **kwargs)

    def clean(self) -> None:
        if self.is_anonymously and self.anonymous_signature == "":
            raise ValidationError("При анонимной отправке нужно указать подпись")
