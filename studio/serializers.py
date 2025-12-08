from rest_framework import serializers
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign, CampaignPost,PublicPost


class CampaignPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignPost
        fields = ('id','title','campaign','pillar','image_prompt','email_subject','email_body',
                  'fb_text','ig_text','pin_title','pin_desc','cta','hashtags','created_at')

    # 👇 This is the important line
        extra_kwargs = {
            "campaign": {"read_only": True}
            # or: "campaign": {"required": False}
        }






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
        read_only_fields = ["id", "created_at", "owner"]


from rest_framework import serializers
from .models import AutoPost

class CMSPostSerializer(serializers.ModelSerializer):
    pillar = serializers.StringRelatedField()  # or customize if you have slug/name
    hashtags_list = serializers.SerializerMethodField()

    class Meta:
        model = AutoPost
        fields = [
            "id",
            "platforms",
            "pillar",
            "topic",
            "vendor_name",
            "language",
            "caption",
            "hashtags",       # raw text like "#thai #food"
            "hashtags_list",  # optional parsed list
            "image_prompt",
            "created_at",
        ]

    def get_hashtags_list(self, obj):
        """
        If you store hashtags as comma- or space-separated text,
        turn them into a list for the frontend.
        """
        if not obj.hashtags:
            return []
        # You can adapt this depending on your format
        parts = obj.hashtags.replace("#", " ").replace("\n", " ").split(",")
        if len(parts) == 1:
            parts = obj.hashtags.replace("#", " ").split()
        return [p.strip() for p in parts if p.strip()]


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


# PORTAL posts

class STMPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "body",
            "image_url",
            "language",
            "published_at",
            "created_at",
        ]




    






    



