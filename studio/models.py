from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

# Create your models here.

from django.contrib.auth import get_user_model

User = get_user_model()

LANG_CHOICES = [
    ("en", "English"),
    ("th", "Thai"),
    ("sv", "Swedish"),
    ("no", "Norwegian"),
]

class Pillar(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    def __str__(self): return self.name






class DesignTemplate(models.Model):
    TEMPLATE_TYPES = [
        ("pinterest_pin", "Pinterest Pin"),
        ("fb_post", "Facebook Post"),
        ("ig_post", "Instagram Post"),
        ("yt_thumb", "YouTube Thumbnail"),
        ("blog_hero", "Blog Hero"),
    ]
    title = models.CharField(max_length=200)
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="design_templates", null=True, blank=True)
    category = models.CharField(max_length=120, blank=True)  # menu, promo, banner, etc.
    thumbnail_url = models.URLField(blank=True)
    canva_url = models.URLField(blank=True)  # link to open in Canva
    tags = models.CharField(max_length=255, blank=True)  # "promo,thai,summer"
    created_at = models.DateTimeField(auto_now_add=True)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    thumbnail = models.URLField(max_length=500, null=True, blank=True)

    ai_tool_key = models.CharField(
        max_length=100,
        help_text="Key for which AI tool / prompt config to use, e.g. 'campaign_pin'"
    )

    def __str__(self):
        return self.tags + " - " + self.title
    

class ReviewReply(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    review_text = models.TextField()
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default="en")
    tone = models.CharField(max_length=100, default="polite")
    reply_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Campaign(models.Model):
    PILLARS = (('Food','Food'),('Game','Game'),('Wellness','Wellness'))
    LANGS = (('en','English'),('sv','Swedish'),('th','Thai'))
    GOALS = (('awareness','Awareness'),('traffic','Traffic'),('engagement','Engagement'))
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    #pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="campaign", null=True, blank=True)
    pillar = models.CharField(max_length=16, choices=PILLARS)
    language = models.CharField(max_length=4, choices=LANGS, default='en')
    goal = models.CharField(max_length=16, choices=GOALS, default='awareness')
    keywords = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Structured outputs
    email_subject = models.CharField(max_length=200, blank=True)
    email_body = models.TextField(blank=True)
    social_caption = models.TextField(blank=True)
    cta = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.title

class CampaignPost(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='posts', on_delete=models.CASCADE)
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="campaignPost", null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    channel = models.CharField(max_length=50, blank=True)
    image_prompt = models.TextField(blank=True)
    email_subject = models.CharField(max_length=255, blank=True)
    email_body = models.TextField(blank=True)
    fb_text = models.TextField(blank=True)
    ig_text = models.TextField(blank=True)
    pin_title = models.CharField(max_length=255, blank=True)
    pin_desc = models.TextField(blank=True)
    cta = models.CharField(max_length=255, blank=True)
    hashtags = models.JSONField(default=list, blank=True)
    designTemplate = models.ForeignKey(DesignTemplate, on_delete=models.CASCADE, related_name="campaignPosts", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.title
    


class PublicPost(models.Model):
    campaign_post = models.OneToOneField(
        "studio.CampaignPost",
        on_delete=models.CASCADE,
        related_name="public_post",
        null=True,
        blank=True,
        help_text="Source AI post this public post was refined from."
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    image_url = models.URLField(blank=True)
    language = models.CharField(max_length=5, default="en")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:40]
            slug = base_slug
            n = 1
            while PublicPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


    




class AutoPost(models.Model):
    PLATFORMS =[
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("stm", "stm"),
    ("linkedin", "LinkedIn"),
    ("tiktok", "TikTok"),
    ]
    LANGS = [("en","English"),("th","Thai"),("sv","Swedish"),("no","Norwegian")]
    
    CampaignPost = models.ForeignKey(CampaignPost, on_delete=models.CASCADE, related_name="autoPosts", null=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    vendor_name = models.CharField(max_length=200, blank=True)
    platforms = models.CharField(max_length=20, choices=PLATFORMS, default="facebook")
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="AutoPost", null=True, blank=True)
    topic = models.CharField(max_length=200)  # e.g. "product", "menu", "promo"
    keywords = models.TextField(blank=True)   # comma list or free text
    tone = models.CharField(max_length=100, blank=True, default="friendly")
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default="en")
    caption = models.TextField(blank=True)
    hashtags = models.TextField(blank=True)
    image_prompt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="pending"  # pending / posted / failed
    )

    def __str__(self):
        return f"{self.topic} ({self.platforms})" if self.topic else f"AutoPost #{self.id}"



class Theme(models.Model):
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="themes")
    name = models.CharField(max_length=150)
    goal = models.CharField(max_length=200, blank=True)  # e.g., “educate”, “SEO”, “traffic”
    notes = models.TextField(blank=True)

    def __str__(self): return f"{self.pillar.name} – {self.name}"

class Topic(models.Model):

    LANGS = [("en","English"),("th","Thai"),("sv","Swedish"),("no","Norwegian")]
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)  # pin/blog title
    keywords = models.CharField(max_length=300, blank=True)
    language = models.CharField(max_length=2, choices=LANGS, default="en")
    status = models.CharField(max_length=30, default="draft")  # draft|generated|approved|scheduled|published
    
    def __str__(self): return self.title

class Asset(models.Model):
    PLATFORMS =[
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("stm", "stm"),
    ("linkedin", "LinkedIn"),
    ("tiktok", "TikTok"),
    ]
 
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="assets")
    platform = models.CharField(max_length=20, choices=PLATFORMS, default="pinterest")
    # Core generated fields
    script = models.TextField(blank=True)             # short script/caption
    seo_title = models.CharField(max_length=70, blank=True)
    seo_desc = models.CharField(max_length=160, blank=True)
    hashtags = models.CharField(max_length=400, blank=True)
    image_prompt = models.TextField(blank=True)
    canva_template_url = models.URLField(blank=True)
    # Publishing metadata
    board = models.CharField(max_length=120, blank=True)     # Pinterest board name
    target_url = models.URLField(blank=True)                  # blog/product page
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    # Tracking (you can fill via manual admin entry first)
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)

    @property
    def ctr(self):
        return (self.clicks / self.impressions) if self.impressions else 0.0
    @property
    def winner(self):
        # simple heuristic, tune later
        return self.saves >= 10 or self.ctr >= 0.04


