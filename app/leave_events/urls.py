from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .views import LeaveNotificationView

router = DefaultRouter()
router.register(r"leave-notifications", LeaveNotificationView, basename="leave-notification")
app_name = "leave_events"
urlpatterns = [
    *router.urls,
    path("leave-messages/", views.messages_list, name="messages_list"),
]
