from django.db import models

ATLAS_WORKSPACE_ID = 1167322787740055
SOURCE_DIV_PROBLEMS_REQUESTS_PROJECT_ID = 1211350261357695
SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID = 1211350376356166

class Position(models.TextChoices):
    BUYER = "buyer", "Баер"
    FARMER = "farmer", "Фармер"
    MANAGER = "manager", "Менеджер"
