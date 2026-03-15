
from django.contrib import admin
from .models import AutoPost,PublicPost, DesignTemplate, ReviewReply, Campaign,CampaignPost,Pillar,Theme,Topic,Asset

class AutoPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'scheduled_time', 'status')
    list_filter = ('owner',)
    search_fields = ('topic', 'caption')

class DesignTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'goal')
    list_filter = ('created_by',)
    search_fields = ('title',)

class CampaignPostAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'title', 'scheduled_time', 'status')
    search_fields = ('title', 'campaign__name')


admin.site.register(AutoPost,AutoPostAdmin)
admin.site.register(PublicPost)
admin.site.register(DesignTemplate)
admin.site.register(ReviewReply)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(CampaignPost)
admin.site.register(Pillar)
admin.site.register(Theme)
admin.site.register(Topic)
admin.site.register(Asset)




