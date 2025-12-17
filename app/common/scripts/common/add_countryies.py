import logging

from common.models import Country

countries = [
    ("AR", "Argentina"),
    ("AU", "Australia"),
    ("BA", "Bosnia and Herzegovina"),
    ("BY", "Belarus"),
    ("CA", "Canada"),
    ("CR", "Costa Rica"),
    ("CL", "Chile"),
    ("DE", "Germany"),
    ("ES", "Spain"),
    ("FR", "France"),
    ("GB", "United Kingdom"),
    ("GR", "Greece"),
    ("IL", "Israel"),
    ("IR", "Iran"),
    ("IT", "Italy"),
    ("JP", "Japan"),
    ("MX", "Mexico"),
    ("NL", "Netherlands"),
    ("PL", "Poland"),
    ("PE", "Peru"),
    ("PT", "Portugal"),
    ("RU", "Russia"),
    ("TR", "Turkey"),
    ("UA", "Ukraine"),
    ("US", "USA"),
]


def run() -> None:
    for code, name in countries:
        obj, created = Country.objects.get_or_create(iso_code=code, defaults={"name": name})
        if created:
            logging.info("Added country %s to %s", code, name)
