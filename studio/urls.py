from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CMSPostListAPIView, AutoPostViewSet, DesignTemplateViewSet, ReviewReplyViewSet, CampaignViewSet,CampaignPostViewSet,STMPostViewSet,PublishFromCampaignAPIView

router = DefaultRouter()
router.register(r"auto-posts", AutoPostViewSet,basename='auto-post')
router.register(r"templates", DesignTemplateViewSet,basename='template')
router.register(r"review-replies", ReviewReplyViewSet,basename='review-reply')
router.register(r"stm-post", STMPostViewSet,basename='stm-post')
router.register("cms-post", CampaignPostViewSet,basename='cms-post')
router.register("campaigns", CampaignViewSet,basename='campaigns')


urlpatterns = [
    path("", include(router.urls)),
    # CMS - posts for STM consumption
    path("cms-posts/", CMSPostListAPIView.as_view(), name="cms-posts"),
    path("publish-from-campaign/<int:campaign_id>/", PublishFromCampaignAPIView.as_view(), name="publish-from-campaign"),
 
]
