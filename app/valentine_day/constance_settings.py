from datetime import datetime

CONSTANCE_CONFIG = {
    "SHOW_VALENTINES_AT": (
        datetime(2026, 2, 13, 14, 0, 0),  # noqa: DTZ001
        "В какое время открыть полученные валентинки",
        "datetime",
    ),
    "SEND_TELEGRAM_NOTIFICATIONS": (
        False,
        "Отправлять уведомление в Telegram при получении валентинки",
        bool,
    ),
    "ALLOW_SENDING_VALENTINES": (
        True,
        "Разрешить пользователям отправлять валентинки",
        bool,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "VALENTINE_DAY": (
        "SHOW_VALENTINES_AT",
        "SEND_TELEGRAM_NOTIFICATIONS",
        "ALLOW_SENDING_VALENTINES",
    ),
}
