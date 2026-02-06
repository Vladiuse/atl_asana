CONSTANCE_CONFIG = {
    "SEND_NOTIFICATION_DELAY": (
        5,
        "Через минут отправлять уведомление",
        int,
    ),
    "SEND_REMINDER_DELAY": (
        14,
        "За сколько дней до отпуска оповещать об этом",
        int,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "EMPLOYEE_LEAVE": (
        "SEND_NOTIFICATION_DELAY",
        "SEND_REMINDER_DELAY",
    ),
}
