from rest_framework import serializers
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign, CampaignPost


class CampaignPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignPost
        fields = ('id','title','campaign','pillar','image_prompt','email_subject','email_body',
                  'fb_text','ig_text','pin_title','pin_desc','cta','hashtags','created_at')

class CampaignSerializer(serializers.ModelSerializer):
    posts = CampaignPostSerializer(many=True)
    class Meta:
        model = Campaign
        fields = ('id','title','overview','pillar','language','goal','keywords','created_at','updated_at','posts',)
    read_only_fields = ("created_at",)


    def create(self, validated_data):
        posts_data = validated_data.pop("posts", [])

        user = self.context["request"].user

        campaign = Campaign.objects.create(created_by=user, **validated_data)
        objs = [
            CampaignPost(
                campaign=campaign,
                title=p.get("title", ""),
                image_prompt=p.get("image_prompt", ""),
                email_subject=p.get("email_subject", ""),
                email_body=p.get("email_body", ""),
                fb_text=p.get("fb_text", ""),
                ig_text=p.get("ig_text", ""),
                pin_title=p.get("pin_title", ""),
                pin_desc=p.get("pin_desc", ""),
                cta=p.get("cta", ""),
                hashtags=p.get("hashtags", []),
            )
            for p in posts_data
        ]
        if objs:
            CampaignPost.objects.bulk_create(objs)
    
        return campaign

class AutoPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoPost
        fields = "__all__"
        read_only_fields = ["caption", "hashtags", "image_prompt", "created_at", "owner"]

class DesignTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignTemplate
        fields = [
            "id", "title", "category", "thumbnail_url","canva_url","tags","created_at","template_type","thumbnail", 
             "ai_tool_key",
        ]

class ReviewReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReply
        fields = "__all__"
        read_only_fields = ["reply_text", "created_at", "owner"]



    



