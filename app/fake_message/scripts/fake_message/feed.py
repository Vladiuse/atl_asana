# ruff : noqa : S311
import random
from datetime import timedelta

from django.utils import timezone
from faker import Faker

from fake_message.models import Handlers, Message, MessageStatus, TgParseMode


def fill_database(n: int = 100) -> None:
    fake: Faker = Faker(["ru_RU"])  # Используем русский язык для текста

    # Получаем списки значений из TextChoices
    parse_modes: list[str] = TgParseMode.values
    tags: list[str] = Handlers.values
    statuses: list[str] = MessageStatus.values

    messages_to_create: list[Message] = []

    for _ in range(n):
        # Генерируем случайную дату отправки (от -7 до +7 дней от текущего момента)
        random_days: int = random.randint(-7, 7)
        random_send_at = timezone.now() + timedelta(days=random_days)

        # Решаем, будет ли send_at пустым (в 30% случаев)
        send_at = random_send_at if random.choice([0, 1]) else None

        msg = Message(
            text=fake.paragraph(nb_sentences=3),  # Генерируем 3 предложения
            parse_mode=random.choice(parse_modes),
            tag=random.choice(tags),
            status=random.choice(statuses),
            send_at=send_at,
        )
        messages_to_create.append(msg)

    # Используем bulk_create для быстрой вставки 100 записей одним запросом
    Message.objects.bulk_create(messages_to_create)
    print(f"Successfully created {n} messages!")


def run() -> None:
    Message.objects.all().delete()
    fill_database()
