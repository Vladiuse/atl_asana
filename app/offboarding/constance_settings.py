CONSTANCE_CONFIG = {
    "DELAY_FOR_FEED_CARD": (
        5,
        "Через сколько поля в каточке оффбординга после создания  будут заполнены (в минутах)",
        int,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "OFFBOARDING": ("DELAY_FOR_FEED_CARD",),
}
