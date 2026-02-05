from django.db import models


class Customer(models.Model):
    image = models.ImageField(
        upload_to="images/",
        blank=True,
        max_length=255,
    )
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    position = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"
