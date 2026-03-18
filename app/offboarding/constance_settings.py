CONSTANCE_CONFIG = {
    "DELAY_FOR_FEED_CARD": (
        5,
        "Через сколько поля в каточке оффбординга после создания  будут заполнены (в минутах)",
        int,
    ),
    "OFFBOARDING_CE_SECTION_ID": (
        "1205707970532975",
        'Айди секции "Done" на доске оффбординга',
        str,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "OFFBOARDING": (
        "DELAY_FOR_FEED_CARD",
        "OFFBOARDING_CE_SECTION_ID",
    ),
}
