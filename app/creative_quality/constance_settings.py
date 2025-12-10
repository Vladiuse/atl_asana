CONSTANCE_CONFIG = {
    "RATE_DELAY": (
        3,
        "Через сколько дней присылать сообщение об оценке креатива",
        int,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "CREATIVE_ESTIMATE": ("RATE_DELAY",),
}
