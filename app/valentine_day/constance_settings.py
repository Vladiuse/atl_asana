CONSTANCE_CONFIG = {
    "SHOW_VALENTINES_AT": (
        None,
        "В какое время открыть полученные валентинки",
        "datetime",
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "VALENTINE_DAY": (
        "SHOW_VALENTINES_AT",
    ),
}
