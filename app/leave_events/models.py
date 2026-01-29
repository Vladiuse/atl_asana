from django.db import models


class LeaveType(models.TextChoices):
    VACATION = "VACATION", "Отпуск"
    DAY_OFF = "DAY_OFF", "Отгул"


class LeaveNotification(models.Model):
    type = models.CharField(max_length=30, choices=LeaveType)
    employee = models.CharField(max_length=254)
    supervisor_tag = models.CharField(max_length=254)
    start_date = models.DateField()
    end_date = models.DateField()
    cancellable_until = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self) -> str:
        return f"{self.employee}:{self.start_date}"
