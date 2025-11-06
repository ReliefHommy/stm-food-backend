from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AutoPostViewSet, DesignTemplateViewSet, ReviewReplyViewSet, CampaignViewSet

router = DefaultRouter()
router.register(r"auto-posts", AutoPostViewSet)
router.register(r"templates", DesignTemplateViewSet)
router.register(r"review-replies", ReviewReplyViewSet)
router.register(r"campaigns", CampaignViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
