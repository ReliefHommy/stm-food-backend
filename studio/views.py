import json
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, generics,status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.response import Response
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign,CampaignPost,PublicPost
from .serializers import (
    AutoPostSerializer, DesignTemplateSerializer,
    ReviewReplySerializer, CampaignSerializer,CampaignPostSerializer,CMSPostSerializer,STMPostSerializer
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
    #permission_classes = [permissions.IsAuthenticated]


class AutoPostViewSet(viewsets.ModelViewSet):
    queryset = AutoPost.objects.all().order_by("-created_at")
    serializer_class = AutoPostSerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None

        # If you want all manually created posts to default to STM + posted:
        platforms = serializer.validated_data.get("platforms") or "stm"
        status = serializer.validated_data.get("status") or "posted"

        serializer.save(
            owner=user,
            platforms=platforms,
            status=status,
        )

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        obj = self.get_object()
        data = json.loads(gen_auto_post(obj.language, obj.topic, obj.keywords, obj.tone))
        obj.caption = data.get("caption", "")
        obj.hashtags = data.get("hashtags", "")
        obj.image_prompt = data.get("image_prompt", "")
        obj.save()
        return Response(AutoPostSerializer(obj).data)
    


class CMSPostListAPIView(generics.ListAPIView):
    queryset = PublicPost.objects.all().order_by("-published_at", "-created_at")
    serializer_class = CMSPostSerializer
    permission_classes = [permissions.IsAuthenticated]  # CMS is private

    def get_queryset(self):
        qs = AutoPost.objects.filter(
            platforms="stm",
            status="posted",   # only published ones
        ).order_by("-created_at")

        lang = self.request.query_params.get("lang")
        pillar = self.request.query_params.get("pillar")

        if lang:
            qs = qs.filter(language=lang)
        if pillar:
            qs = qs.filter(pillar__name=pillar)  # or pillar__slug

        return qs

class DesignTemplateViewSet(viewsets.ModelViewSet):
    queryset = DesignTemplate.objects.all().order_by("-created_at")
    serializer_class = DesignTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

class ReviewReplyViewSet(viewsets.ModelViewSet):
    queryset = ReviewReply.objects.all().order_by("-created_at")
    serializer_class = ReviewReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        obj = self.get_object()
        reply = gen_review_reply(obj.language, obj.tone, obj.review_text)
        obj.reply_text = reply
        obj.save()
        return Response(ReviewReplySerializer(obj).data)



class STMPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PublicPost.objects.filter(is_published=True).order_by("-published_at", "-created_at")
    serializer_class = STMPostSerializer
    permission_classes = [permissions.AllowAny]   # ← PUBLIC



class PublishFromCampaignAPIView(APIView):

    #permission_classes = [permissions.IsAuthenticated]  # protect this!
    permission_classes = [permissions.AllowAny] 

    def post(self, request,campaign_id, *args, **kwargs):
        cp = get_object_or_404(CampaignPost, pk=campaign_id)
        campaign_post_id = campaign_id
        # 1) Take refined values from Studio if present
        refined_title = request.data.get("title")
        refined_excerpt = request.data.get("excerpt")
        refined_body = request.data.get("body")
        refined_image_url = request.data.get("image_url")

        # 2) Fallbacks from CampaignPost if not provided

        title = refined_title or cp.title or cp.pin_title or cp.email_subject or ""
        excerpt = refined_excerpt or (cp.fb_text or getattr(cp, "pin_desc", "") or "")[:160]
        body = refined_body or cp.email_body or cp.fb_text or getattr(cp, "pin_desc", "") or ""

        if refined_image_url:
            image_url = refined_image_url
        elif getattr(cp, "designTemplate", None) and getattr(cp.designTemplate, "image_url", None):
            image_url = cp.designTemplate.image_url
        else:
            image_url = ""

        language = getattr(cp.campaign, "language", "en")

        # 3) Create or update snapshot PublicPost
        pp, created = PublicPost.objects.update_or_create(
            campaign_post=cp,
            defaults={
                "title": title,
                "excerpt": excerpt,
                "body": body,
                "image_url": image_url,
                "language": language,
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        serializer = STMPostSerializer(pp)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
    
# Optional: allow GET from browser for quick testing
    def get(self, request, campaign_id, *args, **kwargs):
        return self.post(request, campaign_id, *args, **kwargs)    
    
    

       

      

    
        



