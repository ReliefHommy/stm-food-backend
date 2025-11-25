from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AutoPostViewSet, DesignTemplateViewSet, ReviewReplyViewSet, CampaignViewSet,CampaignPostViewSet

router = DefaultRouter()
router.register(r"auto-posts", AutoPostViewSet,basename='auto-post')
router.register(r"templates", DesignTemplateViewSet,basename='template')
router.register(r"review-replies", ReviewReplyViewSet,basename='review-reply')
router.register("campaigns-post", CampaignPostViewSet,basename='campaign-post')
router.register("campaigns", CampaignViewSet,basename='campaigns')


urlpatterns = [
    path("", include(router.urls)),
]
