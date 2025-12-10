from enum import Enum

from django.db import models

ATLAS_WORKSPACE_ID = 1167322787740055


class AtlasProject(Enum):
    SOURCE_DIV_PROBLEMS_REQUESTS = "1211350261357695"
    TECH_DIV_KVA = "1210393628043121"


class Position(models.TextChoices):
    BUYER = "buyer", "Баер"
    FARMER = "farmer", "Фармер"
    MANAGER = "manager", "Менеджер"
    DESIGNER = "designer", "Дизайнер"


class AsanaResourceType(models.TextChoices):
    PROJECT = "project", "Проект"
    SECTION = "section", "Секция"
