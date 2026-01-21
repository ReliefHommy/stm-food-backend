from django.urls import path
from .admin_views import AdminUserMetricsView,AdminUserListView

urlpatterns = [
    path("metrics/users/", AdminUserMetricsView.as_view(), name="admin-user-metrics"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
]
