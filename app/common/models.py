from django.db import models


class Country(models.Model):
    iso_code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name
