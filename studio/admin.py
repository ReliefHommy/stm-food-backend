
import json
from .ai import gen_campaign, gen_auto_post, gen_review_reply

from django.contrib import admin
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign,CampaignPost,Pillar,Theme,Topic,Asset

admin.site.register(AutoPost)
admin.site.register(DesignTemplate)
admin.site.register(ReviewReply)
admin.site.register(Campaign)
admin.site.register(CampaignPost)
admin.site.register(Pillar)
admin.site.register(Theme)
admin.site.register(Topic)
admin.site.register(Asset)

@admin.action(description="Generate campaign with AI")
def generate_campaign_action(modeladmin, request, queryset):
    for obj in queryset:
        data = json.loads(gen_campaign(obj.language, obj.keywords, obj.goal))
        obj.email_subject = data.get("email_subject", "")
        obj.email_body = data.get("email_body", "")
        obj.social_caption = data.get("social_caption", "")
        obj.cta = data.get("cta", "")
        obj.save()


@admin.action(description="Generate evergreen campaign with AI")
def generate_evergreen_campaign_action(modeladmin, request, queryset):
    for obj in queryset:
        data = json.loads(gen_campaign(obj.language, obj.keywords, obj.goal, evergreen=True))
        obj.email_subject = data.get("email_subject", "")
        obj.email_body = data.get("email_body", "")
        obj.social_caption = data.get("social_caption", "")
        obj.cta = data.get("cta", "")

        assets = data.get("assets", {})
        obj.pinterest_script = assets.get("pinterest", {}).get("script", "")
        # ...map other fields if you added them to the model...
        obj.save()


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "language", "created_by", "created_at")
    actions = [generate_campaign_action, generate_evergreen_campaign_action]

@admin.action(description="Generate auto post with AI")
def generate_auto_post_action(modeladmin, request, queryset):
    for obj in queryset:
        data = json.loads(gen_auto_post(obj.language, obj.topic, obj.keywords, obj.tone))
        obj.caption = data.get("caption", "")
        obj.hashtags = data.get("hashtags", "")
        obj.image_prompt = data.get("image_prompt", "")
        obj.save()


@admin.register(AutoPost)
class AutoPostAdmin(admin.ModelAdmin):
    list_display = ("id", "language", "topic", "created_at")
    actions = [generate_auto_post_action]


@admin.action(description="Generate reply with AI")
def generate_reply_action(modeladmin, request, queryset):
    for obj in queryset:
        reply = gen_review_reply(obj.language, obj.tone, obj.review_text)
        obj.reply_text = reply
        obj.save()


@admin.register(ReviewReply)
class ReviewReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "language", "tone", "created_at")
    actions = [generate_reply_action]
    list_display = ("id", "language", "tone", "created_at")
    actions = [generate_reply_action]

