CONSTANCE_CONFIG = {
    "NEED_RATED_AT": (
        3,
        "Через сколько дней присылать сообщение об оценке креатива",
        int,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "CREATIVE_ESTIMATE": ("NEED_RATED_AT",),
}
