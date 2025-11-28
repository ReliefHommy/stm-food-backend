
from django.contrib import admin
from .models import AutoPost, DesignTemplate, ReviewReply, Campaign,CampaignPost,Pillar,Theme,Topic,Asset

class AutoPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_time', 'status')
    search_fields = ('title', 'content')

class DesignTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'status')
    search_fields = ('name',)

class CampaignPostAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'title', 'scheduled_time', 'status')
    search_fields = ('title', 'campaign__name')


admin.site.register(AutoPost)
admin.site.register(DesignTemplate)
admin.site.register(ReviewReply)
admin.site.register(Campaign)
admin.site.register(CampaignPost)
admin.site.register(Pillar)
admin.site.register(Theme)
admin.site.register(Topic)
admin.site.register(Asset)




