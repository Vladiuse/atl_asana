from django.db import models


class TgParseMode(models.TextChoices):
    HTML = "HTML", "HTML"
    MARKDOWN = "Markdown", "MarkdownV2"
    PLAIN = "Plain", "Plain Text"


class Handlers(models.TextChoices):
    DOMAIN_HANDLER = "domain_check", "Domain Check"
    KVA_USER = "kva_test", "KVA Test"
    FARM_GROUP = "asana_farm_comments", "Asana Farm Comments"
    SMS_SERVICE_BALANCE = "p1sms_balance", "P1SMS Balance"
    OFFER_AWAKEN = "offer_reawake", "Offer Reawake"
    ONBOARDING = "onboarding", "Onboarding"
    HR_VACATION = "hr_vacation", "HR Vacation"
    LUCK_STAR_ACCOUNTS = "luckstar_accounts", "Luckstar Accounts"


class MessageStatus(models.TextChoices):
    PENDING = "pending", "В очереди"
    SENT = "sent", "Отправлено"
    ERROR = "error", "Ошибка"


class Message(models.Model):
    text = models.TextField()
    parse_mode = models.CharField(
        max_length=30,
        choices=TgParseMode.choices,
    )
    tag = models.CharField(
        max_length=30,
        choices=Handlers.choices,
    )
    status = models.CharField(
        max_length=15,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING,
    )
    send_at = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Сообщение Telegram"
        verbose_name_plural = "Сообщения Telegram"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.text
