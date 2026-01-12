CONSTANCE_CONFIG = {
    "DESIGN_TASK_BAYER_CUSTOM_FIELD_NAME": (
        "Инициалы Баера",
        "Название поля с указанием баера в таске на досках дизайна",
        str,
    ),
    "DESIGN_TASK_LINK_ON_WORK_FIELD_NAME": (
        "Ссылка на работу",
        "Название поля с указанием ссылки на работу в таске на досках дизайна",
        str,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "ASANA": ("DESIGN_TASK_BAYER_CUSTOM_FIELD_NAME", "DESIGN_TASK_LINK_ON_WORK_FIELD_NAME"),
}
