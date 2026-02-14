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
    "LEAVE_TABLE_URL": (
        str,
        "Ссылка на табличку с отпусками",
        "https://docs.google.com/spreadsheets/d/1bbo6WxBLGk24FeSRucCYkwuWu1cYafb_5XsVgBO1DnY/edit?gid=570923352#gid=570923352",
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "EMPLOYEE_LEAVE": (
        "SEND_NOTIFICATION_DELAY",
        "SEND_REMINDER_DELAY",
    ),
}
