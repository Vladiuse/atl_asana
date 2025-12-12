CONSTANCE_CONFIG = {
    "NEED_RATED_AT": (
        3,
        "Через сколько дней присылать сообщение об оценке креатива",
        int,
    ),
    "NEXT_SUCCESS_REMINDER_DELTA": (
        24,
        "Через сколько часов отправлять повторное смс об оценке креатива",
        int,
    ),
    "FAILURE_RETRY_INTERVAL": (
        2,
        "Через сколько часов попытаться отправит смс об оценке при ошибке отправки",
        int,
    ),
    "SEND_REMINDER_TRY_COUNT": (
        3,
        "Число попыток для отправки сообщений, успешных и нет",
        int,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "CREATIVE_ESTIMATE": (
        "NEED_RATED_AT",
        "NEXT_SUCCESS_REMINDER_DELTA",
        "FAILURE_RETRY_INTERVAL",
    ),
}
