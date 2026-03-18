CONSTANCE_CONFIG = {
    "DELAY_FOR_FEED_CARD": (
        5,
        "Через сколько поля в каточке оффбординга после создания  будут заполнены (в минутах)",
        int,
    ),
    "OFFBOARDING_COMPLETE_SECTION_ID": (
        "1205707970532975",
        'Айди секции "Done" на доске оффбординга',
        str,
    ),
    "TARGET_SUB_TASKS_NAMES": (
        "Сделать расчет по зп,Провести Exit интервью",
        "Название сабтасок которые должны остаться, когда все остальные завершены для отправки оповещения",
        str,
    )
}

CONSTANCE_CONFIG_FIELDSETS = {
    "OFFBOARDING": (
        "DELAY_FOR_FEED_CARD",
        "OFFBOARDING_COMPLETE_SECTION_ID",
    ),
}
