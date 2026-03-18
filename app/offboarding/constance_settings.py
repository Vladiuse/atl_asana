from message_sender.client import Handlers

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
    ),
    "PAYROLL_RESPONSIBLE_TELEGRAM_LOGIN": (
        "@xxx",
        "Телеграм логин ответственного за расчет сотрудника при оффбординге",
        str,
    ),
    "OFFBOARDING_NOTIFY_HANDLER": (
        Handlers.KVA_USER.value,
        "В какой чат отправлять уведомления",
        "message_sender_handler",
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "OFFBOARDING": (
        "DELAY_FOR_FEED_CARD",
        "OFFBOARDING_COMPLETE_SECTION_ID",
        "TARGET_SUB_TASKS_NAMES",
        "PAYROLL_RESPONSIBLE_TELEGRAM_LOGIN",
        "OFFBOARDING_NOTIFY_HANDLER",
    ),
}
