from datetime import timedelta
from typing import Any

from django.utils import timezone
from message_sender.models import ScheduledMessage

from .models import LeaveNotification


class LeaveNotificationService:
    def create_notifications(self, validated_data: dict[str, Any]) -> LeaveNotification:
        leave, created = LeaveNotification.objects.get_or_create(
            employee=validated_data["employee"],
            start_date=validated_data["start_date"],
            type=validated_data["type"],
            defaults={
                "supervisor_tag": validated_data["supervisor_tag"],
                "end_date": validated_data["end_date"],
                "cancellable_until": timezone.now() + timedelta(minutes=5),
            },
        )
        if not created:
            return leave
        ScheduledMessage.objects.create(
            run_at=timezone.now() + timedelta(minutes=5),
            text=f"Отпуск создан: {leave.start_date} – {leave.end_date}",
            user_tag="kva_tech",
            reference_id=f"leave-{leave.pk}",
        )
        ScheduledMessage.objects.create(
            run_at=leave.start_date - timedelta(weeks=2),
            text=f"Напоминание: отпуск с {leave.start_date} по {leave.end_date}",
            user_tag="kva_tech",
            reference_id=f"leave-{leave.pk}",
        )
        return leave

    def cancel_notifications(self, leave: LeaveNotification) -> None:
        ScheduledMessage.objects.filter(reference_id=f"leave-{leave.pk}").delete()