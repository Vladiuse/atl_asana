from django.db import models

ATLAS_WORKSPACE_ID = 1167322787740055


class Position(models.TextChoices):
    BUYER = "buyer", "Баер"
    FARMER = "farmer", "Фармер"
    MANAGER = "manager", "Менеджер"
