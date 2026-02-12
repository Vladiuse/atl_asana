from turtle import mode
from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet
from rest_framework.authtoken.models import Token
from transliterate import translit


class EmployeeQuerySet(models.QuerySet["Employee"]):
    def delete(self) -> tuple[int, dict[str, int]]:
        users = [e.user for e in self.select_related("user")]
        delete_result = super().delete()
        for user in users:
            user.delete()
        return delete_result


class EmployeeManager(models.Manager):  # type: ignore[type-arg]
    def get_queryset(self) -> QuerySet["Employee"]:
        return EmployeeQuerySet(self.model, using=self._db)


class Employee(models.Model):
    is_open_app = models.BooleanField(
        default=False,
    )
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
    )
    telegram_user_id = models.CharField(
        max_length=30,
        unique=True,
    )
    telegram_login = models.CharField(
        max_length=30,
        blank=True,
    )
    avatar = models.ImageField(
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
    sub_1 = models.CharField(
        max_length=30,
        blank=True,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    objects = EmployeeManager()

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    def save(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        if not self.pk:
            full_name = f"{self.name}_{self.surname}"
            username = translit(full_name, "ru", reversed=True).replace(" ", "_").lower()
            self.user = User.objects.create_user(username=username, password="0000")  # noqa: S106
            Token.objects.create(user=self.user)
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        user = self.user
        delete_result = super().delete(*args, **kwargs)
        user.delete()
        return delete_result


class ValentineImage(models.Model):
    image = models.ImageField(
        upload_to="valentine_day/images/for_valentines",
        max_length=255,
    )
    owner = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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
    is_read_by_recipient = models.BooleanField(
        default=False,
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
