from asana.models import AtlasAsanaUser
from common.models import Country
from constance import config
from django.db import models, transaction
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone


class TaskManager(models.Manager["Task"]):
    def needs_update(self) -> QuerySet["Task"]:
        return self.get_queryset().filter(
            status__in=[TaskStatus.PENDING, TaskStatus.ERROR_LOAD_INFO],
            load_failure_count__lt=config.TASK_MAX_LOAD_FAILURES,
        )

    def error_load_info(self) -> QuerySet["Task"]:
        return self.get_queryset().filter(
            status=TaskStatus.ERROR_LOAD_INFO,
            load_failure_count__gte=config.TASK_MAX_LOAD_FAILURES,
        )


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    DELETED = "deleted", "Удален"
    CREATED = "created", "Создан"
    ERROR_LOAD_INFO = "error_load_info", "Ошибка загрузки"


class Task(models.Model):
    REQUIRED_FOR_ESTIMATION = ("assignee_id", "bayer_code")

    task_id = models.CharField(
        max_length=20,
        unique=True,
    )
    is_completed = models.BooleanField(
        default=False,
    )
    task_name = models.CharField(
        max_length=254,
        blank=True,
    )
    status = models.CharField(
        max_length=30,
        choices=TaskStatus,
        default=TaskStatus.PENDING,
    )
    assignee_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Исполнитель",
    )
    bayer_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Код баера",
    )
    url = models.CharField(
        max_length=254,
        blank=True,
    )
    work_url = models.CharField(
        max_length=254,
        blank=True,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    load_failure_count = models.PositiveIntegerField(default=0)

    objects = TaskManager()

    def __str__(self) -> str:
        return self.task_id

    def get_assignee_display(self) -> str:
        value = self.assignee_id
        try:
            name = AtlasAsanaUser.objects.get(user_id=self.assignee_id).name
            if name:
                value = name
        except AtlasAsanaUser.DoesNotExist:
            pass
        return value

    def mark_deleted(self) -> None:
        with transaction.atomic():
            self.status = TaskStatus.DELETED
            self.save()
            if hasattr(self, "creative"):
                self.creative.cancel_estimation()

    def mark_error_load_info(self, *, save: bool = True) -> None:
        self.status = TaskStatus.ERROR_LOAD_INFO
        self.load_failure_count += 1
        if save:
            self.save()


class CreativeManager(models.Manager["Creative"]):
    def overdue_for_estimate(self) -> QuerySet["Creative"]:
        return self.get_queryset().filter(
            status=CreativeStatus.WAITING,
            need_rated_at__lte=timezone.now(),
        )

    def need_send_estimate_message(self) -> QuerySet["Creative"]:
        return self.get_queryset().filter(
            status=CreativeStatus.NEED_ESTIMATE,
            next_reminder_at__lte=timezone.now(),
        )

    def need_send_to_gsheet(self) -> QuerySet["Creative"]:
        return self.get_queryset().filter(
            status=CreativeStatus.RATED,
            gsheet_sent=False,
        )


class CreativeStatus(models.TextChoices):
    WAITING = "waiting", "Ожидает"
    NEED_ESTIMATE = "need_review", "Нужна оценка"
    RATED = "rated", "Оценено"
    REMINDER_LIMIT_REACHED = "reminder_limit_reached", "Лимит напоминаний достигнут"
    CANCELED = "canceled", "Оценка отменена"
    EXPIRED = "expired", "Просрочено"


class Creative(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="creative")
    status = models.CharField(max_length=50, choices=CreativeStatus, default=CreativeStatus.WAITING)
    need_rated_at = models.DateTimeField(null=True)
    gsheet_sent = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    next_reminder_at = models.DateTimeField(null=True, blank=True)
    reminder_success_count = models.PositiveIntegerField(default=0)
    reminder_failure_count = models.PositiveIntegerField(default=0)
    reminder_fail_reason = models.TextField(blank=True)

    objects = CreativeManager()

    def __str__(self) -> str:
        return f"<Creative:{self.task}>"

    def mark_rated(self, *, save: bool = True) -> None:
        self.status = CreativeStatus.RATED
        self.next_reminder_at = None
        if save:
            self.save()

    def mark_need_estimate(self, *, save: bool = True) -> None:
        self.status = CreativeStatus.NEED_ESTIMATE
        self.next_reminder_at = timezone.now()
        if save:
            self.save()

    def mark_reminder_limit_reached(self, *, save: bool = True) -> None:
        self.status = CreativeStatus.REMINDER_LIMIT_REACHED
        self.next_reminder_at = None
        if save:
            self.save()

    def cancel_estimation(self, *, save: bool = True) -> None:
        self.status = CreativeStatus.CANCELED
        self.need_rated_at = None
        if save:
            self.save()

    def is_can_be_updated(self) -> bool:
        return self.status != CreativeStatus.RATED

    def get_estimate_url(self, domain: str | None = None) -> str:
        url = reverse(
            "creative_quality:creative_detail",
            kwargs={"creative_pk": self.pk, "task_id": self.task.task_id},
        )
        if domain:
            return f"https://{domain}{url}"
        return url


class CreativeAdaptation(models.Model):
    creative = models.ForeignKey(
        to=Creative,
        on_delete=models.CASCADE,
        related_name="adaptations",
        related_query_name="adaptation",
    )
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"<CreativeAdaptation:{self.name}>"


class CreativeGeoDataStatus(models.TextChoices):
    ZASHEL = "зашел", "Зашел"
    NE_ZASHEL = "незашел", "Не зашел"


class CreativeGeoData(models.Model):
    creative_adaptation = models.ForeignKey(CreativeAdaptation, on_delete=models.CASCADE, related_name="geo_data")
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    hook = models.FloatField()
    hold = models.FloatField()
    ctr = models.FloatField()
    status = models.CharField(max_length=50, choices=CreativeGeoDataStatus)
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("creative_adaptation", "country")

    def __str__(self) -> str:
        return f"{self.country}-{self.creative_adaptation}"


class CreativeProjectSection(models.Model):
    section_id = models.CharField(max_length=30)
    section_name = models.CharField(max_length=254, blank=True)
    project_name = models.CharField(max_length=254, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.section_name if self.section_name else self.section_id
