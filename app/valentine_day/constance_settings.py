from datetime import datetime

CONSTANCE_CONFIG = {
    "SHOW_VALENTINES_AT": (
        datetime(2026, 2, 13, 14, 0, 0),  # noqa: DTZ001
        "В какое время открыть полученные валентинки",
        "datetime",
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "VALENTINE_DAY": ("SHOW_VALENTINES_AT",),
}
