from rest_framework.routers import DefaultRouter

from .views import LeaveNotificationView

router = DefaultRouter()
router.register(r"leave-notifications", LeaveNotificationView, basename="leave-notification")
app_name = "leave_events"
urlpatterns = [
    *router.urls,
]
