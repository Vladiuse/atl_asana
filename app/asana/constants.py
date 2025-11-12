from enum import Enum

from django.db import models

ATLAS_WORKSPACE_ID = 1167322787740055


class AtlasProject(Enum):
    SOURCE_DIV_PROBLEMS_REQUESTS = "1211350261357695"
    TECH_DIV_KVA = "1210393628043121"


SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID = "1211350376356166"
TECH_DIV_KVA_PROJECT_COMPLETE_SECTION_ID = "1210393628043136"


class Position(models.TextChoices):
    BUYER = "buyer", "Баер"
    FARMER = "farmer", "Фармер"
    MANAGER = "manager", "Менеджер"
