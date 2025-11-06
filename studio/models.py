from django.db import models

# Create your models here.

from django.contrib.auth import get_user_model

User = get_user_model()

LANG_CHOICES = [
    ("en", "English"),
    ("th", "Thai"),
    ("sv", "Swedish"),
    ("no", "Norwegian"),
]

class AutoPost(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    vendor_name = models.CharField(max_length=200, blank=True)
    topic = models.CharField(max_length=200)  # e.g. "product", "menu", "promo"
    keywords = models.TextField(blank=True)   # comma list or free text
    tone = models.CharField(max_length=100, blank=True, default="friendly")
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default="en")
    caption = models.TextField(blank=True)
    hashtags = models.TextField(blank=True)
    image_prompt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DesignTemplate(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=120, blank=True)  # menu, promo, banner, etc.
    thumbnail_url = models.URLField(blank=True)
    canva_url = models.URLField()  # link to open in Canva
    tags = models.CharField(max_length=255, blank=True)  # "promo,thai,summer"
    created_at = models.DateTimeField(auto_now_add=True)

class ReviewReply(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    review_text = models.TextField()
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default="en")
    tone = models.CharField(max_length=100, default="polite")
    reply_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Campaign(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    goal = models.CharField(max_length=120)  # promotion | new_product | event | holiday
    keywords = models.TextField(blank=True)
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default="en")
    # Structured outputs
    email_subject = models.CharField(max_length=200, blank=True)
    email_body = models.TextField(blank=True)
    social_caption = models.TextField(blank=True)
    cta = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

PLATFORMS =[
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("stm", "stm"),
    ("linkedin", "LinkedIn"),
    ("tiktok", "TikTok"),
]
LANGS = [("en","English"),("th","Thai"),("sv","Swedish"),("no","Norwegian")]


class Pillar(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    def __str__(self): return self.name

class Theme(models.Model):
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="themes")
    name = models.CharField(max_length=150)
    goal = models.CharField(max_length=200, blank=True)  # e.g., “educate”, “SEO”, “traffic”
    notes = models.TextField(blank=True)
    def __str__(self): return f"{self.pillar.name} – {self.name}"

class Topic(models.Model):
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)  # pin/blog title
    keywords = models.CharField(max_length=300, blank=True)
    language = models.CharField(max_length=2, choices=LANGS, default="en")
    status = models.CharField(max_length=30, default="draft")  # draft|generated|approved|scheduled|published
    def __str__(self): return self.title

class Asset(models.Model):
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


