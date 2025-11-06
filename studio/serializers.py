from rest_framework import serializers
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign

class AutoPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoPost
        fields = "__all__"
        read_only_fields = ["caption", "hashtags", "image_prompt", "created_at", "owner"]

class DesignTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignTemplate
        fields = "__all__"

class ReviewReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReply
        fields = "__all__"
        read_only_fields = ["reply_text", "created_at", "owner"]

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"
        read_only_fields = ["email_subject", "email_body", "social_caption", "cta", "created_at", "owner"]
