import json
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign,CampaignPost
from .serializers import (
    AutoPostSerializer, DesignTemplateSerializer,
    ReviewReplySerializer, CampaignSerializer,CampaignPostSerializer
)
from .ai import gen_auto_post, gen_review_reply, gen_campaign



class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Campaign.objects.filter(created_by=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save()  # created_by set in serializer.create()




    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        obj = self.get_object()
        evergreen = bool(request.data.get("evergreen"))  # or from query params
        data = json.loads(gen_campaign(obj.language, obj.keywords, obj.goal))
        obj.email_subject = data.get("email_subject", "")
        obj.email_body = data.get("email_body", "")
        obj.social_caption = data.get("social_caption", "")
        obj.cta = data.get("cta", "")
        obj.save()
        return Response(CampaignSerializer(obj).data)
    
class CampaignPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CampaignPost.objects.all().order_by("-created_at")
    serializer_class = CampaignPostSerializer
    permission_classes = [permissions.AllowAny]  # keep simple for now


class AutoPostViewSet(viewsets.ModelViewSet):
    queryset = AutoPost.objects.all().order_by("-created_at")
    serializer_class = AutoPostSerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        obj = self.get_object()
        data = json.loads(gen_auto_post(obj.language, obj.topic, obj.keywords, obj.tone))
        obj.caption = data.get("caption", "")
        obj.hashtags = data.get("hashtags", "")
        obj.image_prompt = data.get("image_prompt", "")
        obj.save()
        return Response(AutoPostSerializer(obj).data)

class DesignTemplateViewSet(viewsets.ModelViewSet):
    queryset = DesignTemplate.objects.all().order_by("-created_at")
    serializer_class = DesignTemplateSerializer

class ReviewReplyViewSet(viewsets.ModelViewSet):
    queryset = ReviewReply.objects.all().order_by("-created_at")
    serializer_class = ReviewReplySerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        obj = self.get_object()
        reply = gen_review_reply(obj.language, obj.tone, obj.review_text)
        obj.reply_text = reply
        obj.save()
        return Response(ReviewReplySerializer(obj).data)



