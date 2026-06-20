from django.urls import path, include
from rest_framework.routers import DefaultRouter

from hello_world.support import views, api_views, admin_dashboard_views

router = DefaultRouter()
router.register(r"api/complaints", api_views.ComplaintViewSet, basename="api-complaint")
router.register(r"api/profiles", api_views.SupportProfileViewSet, basename="api-profile")
router.register(r"api/comments", api_views.ComplaintCommentViewSet, basename="api-comment")
router.register(r"api/audit-logs", api_views.AuditLogViewSet, basename="api-audit-log")

app_name = "support"

urlpatterns = [
    # Web Views
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("admin/dashboard/", admin_dashboard_views.admin_dashboard, name="admin_dashboard"),
    path("complaints/", views.complaint_list, name="complaint_list"),
    path("complaints/new/", views.complaint_create, name="complaint_create"),
    path("complaints/<int:pk>/", views.complaint_detail, name="complaint_detail"),
    path("users/new/", views.user_create, name="user_create"),
    # API Routes
    path("", include(router.urls)),
]
