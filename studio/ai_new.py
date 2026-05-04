import os
import json
from openai import OpenAI
from django.conf import settings


def get_client():
    api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


STM_SYSTEM_CONTEXT = """
You are a content strategist for STM, a Thai culture and experience discovery platform
connecting Europe and Bangkok.

STM helps people discover:
- Thai cultural events in Europe
- Bangkok pop-ups, food experiences, markets, festivals, wellness, and creative happenings
- travel-timed experiences for people planning a Thailand trip
- curated local experiences, not just mass tourism attractions

Write for SEO + AIO (AI answer optimization), not just social media.
That means your outputs must be:
- clear
- specific
- structured
- location-aware
- useful for both human readers and AI-powered search systems

Avoid generic hype. Prefer practical, trustworthy language.
"""


def chat_json(user_prompt: str, fallback: dict) -> str:
    client = get_client()
    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": STM_SYSTEM_CONTEXT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return rsp.choices[0].message.content
    except Exception:
        return json.dumps(fallback, ensure_ascii=False)


def chat_text(user_prompt: str, fallback: str) -> str:
    client = get_client()
    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": STM_SYSTEM_CONTEXT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return rsp.choices[0].message.content.strip()
    except Exception:
        return fallback


def gen_auto_post(language, topic, keywords, tone):
    """
    Generates a social-first asset, but aligned with STM's new discovery positioning.
    Backward-friendly: still returns JSON string.
    """
    prompt = f"""
    Create a discovery-focused social post in {language}.

    Topic: {topic}
    Keywords/context: {keywords}
    Tone: {tone}

    Return valid JSON with keys:
    - caption: 80-140 words, useful and concrete
    - hashtags: 8-12 hashtags, comma separated
    - image_prompt: visual prompt for Canva or image generation
    - reel_hook: short 1-line hook for short video
    - ai_summary: 1-2 sentence answer-style summary suitable for AI/search snippets
    - audience: short phrase describing who this is for
    """
    fallback = {
        "caption": "Discover Thai-connected experiences with STM. Explore events, markets, food, and culture across Europe and Bangkok.",
        "hashtags": "#STM #BangkokEvents #ThaiCulture #ThailandTravel #ThaiEvents #BangkokGuide #EuropeEvents #ThaiLifestyle",
        "image_prompt": "A clean modern collage of Thai cultural experiences in Europe and Bangkok, including markets, food, festivals, and city discovery.",
        "reel_hook": "Discover Thai-connected experiences across Europe and Bangkok.",
        "ai_summary": "STM helps people discover Thai cultural events and curated Bangkok experiences for travelers and culture seekers.",
        "audience": "Travelers, Thai culture seekers, and people moving between Europe and Thailand"
    }
    return chat_json(prompt, fallback)


def gen_review_reply(language, tone, review_text):
    prompt = f"""
    Write a culturally appropriate, polite reply in {language}.

    Tone: {tone}
    Customer review: {review_text}

    Keep it under 120 words.
    Sound warm, respectful, and human.
    """
    fallback = "Thank you for your feedback. We truly appreciate your support and hope to welcome you again soon."
    return chat_text(prompt, fallback)


def gen_discovery_page(language, page_type, location, keywords, audience, tone="clear, modern, trustworthy"):
    """
    New function:
    Generate SEO + AIO assets for STM landing/discovery pages.
    Example page_type:
    - this_week_in_bangkok
    - thai_food_experiences
    - markets_and_popups
    - wellness_experiences
    - creative_bangkok
    - festival_calendar
    - near_bts_mrt
    - bangkok_3_day_guide
    - thai_culture_seekers
    - thai_events_in_europe
    """
    prompt = f"""
    Create a discovery landing page content pack in {language}.

    Page type: {page_type}
    Location: {location}
    Keywords/context: {keywords}
    Audience: {audience}
    Tone: {tone}

    Return valid JSON with keys:
    - seo_title: <= 70 chars
    - seo_desc: <= 160 chars
    - slug_suggestion
    - hero_title
    - hero_subtitle
    - intro: 80-140 words
    - ai_summary: 2-3 sentences, answer-style and citation-friendly in tone
    - key_highlights: array of 4-6 short bullets
    - faq: array of 3 items, each with question and answer
    - related_queries: array of 5 search-style queries
    - social_caption: 60-100 words
    - reel_hook
    - image_prompt
    """
    fallback = {
        "seo_title": f"Discover {location} with STM",
        "seo_desc": f"Explore Thai-connected experiences, events, culture, and local discoveries in {location} with STM.",
        "slug_suggestion": f"{location.lower().replace(' ', '-')}-discovery",
        "hero_title": f"Discover {location}",
        "hero_subtitle": "Curated Thai-connected experiences, culture, and local discovery",
        "intro": f"STM helps travelers and culture seekers explore curated experiences in {location}, from food and markets to festivals, wellness, and creative neighborhoods.",
        "ai_summary": f"STM is a Thai culture and experience discovery platform that helps people find curated experiences in {location}. It focuses on useful, locally flavored discovery rather than mass-tourism listings.",
        "key_highlights": [
            "Curated local discovery",
            "Thai culture and lifestyle angle",
            "Travel-friendly ideas",
            "Useful for planning and inspiration"
        ],
        "faq": [
            {
                "question": f"What can I discover in {location} with STM?",
                "answer": "Food experiences, markets, festivals, wellness spots, and culture-led recommendations."
            },
            {
                "question": "Who is this page for?",
                "answer": "Travelers, culture seekers, and people interested in Thai-connected experiences."
            },
            {
                "question": "What makes STM different?",
                "answer": "STM focuses on curated local experiences and Thai cultural connection, not generic mass listings."
            }
        ],
        "related_queries": [
            f"things to do in {location}",
            f"{location} cultural experiences",
            f"{location} local markets",
            f"{location} wellness experiences",
            f"{location} travel guide"
        ],
        "social_caption": f"Explore curated experiences in {location} with STM — from food and festivals to wellness and local culture.",
        "reel_hook": f"Here’s a better way to discover {location}.",
        "image_prompt": f"A modern lifestyle travel scene in {location} showing food, markets, culture, and local discovery."
    }
    return chat_json(prompt, fallback)


def gen_campaign(language, keywords, goal, evergreen=False, campaign_type="discovery"):
    """
    Backward-compatible but repositioned for STM's SEO + AIO strategy.

    campaign_type examples:
    - discovery
    - editorial
    - seasonal
    - event_promo
    - travel_guide
    """
    if evergreen:
        prompt = f"""
        Create an evergreen STM campaign in {language}.

        Campaign type: {campaign_type}
        Goal: {goal}
        Keywords/context: {keywords}

        Return valid JSON with BOTH:

        1) Backward-compatible keys:
        - email_subject
        - email_body (150-220 words)
        - social_caption (80-120 words)
        - cta

        2) SEO + AIO structured assets:
        - ai_summary: 2-3 sentences answering the core user intent
        - page_intro: 100-160 words
        - faq: array of 3 items with question and answer
        - related_queries: array of 5 search-style queries

        3) assets:
        {{
          "pinterest": {{
            "script": "2-3 sentence caption in {language}",
            "hashtags": "8-12 hashtags, comma separated",
            "seo_title": "<=70 chars",
            "seo_desc": "<=160 chars",
            "image_prompt": "clear visual prompt"
          }},
          "blog": {{
            "title": "editorial title",
            "script": "500-800 words with H2/H3 structure",
            "seo_title": "<=70 chars",
            "seo_desc": "<=160 chars",
            "excerpt": "2-3 sentence summary"
          }},
          "landing_page": {{
            "hero_title": "clear page heading",
            "hero_subtitle": "supporting line",
            "intro": "100-160 words",
            "key_highlights": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"]
          }}
        }}

        Ensure useful, non-generic content. Return valid JSON only.
        """
    else:
        prompt = f"""
        Create an STM campaign in {language}.

        Campaign type: {campaign_type}
        Goal: {goal}
        Keywords/context: {keywords}

        Return valid JSON with keys:
        - email_subject
        - email_body (150-220 words)
        - social_caption (80-120 words)
        - cta
        - ai_summary
        - reel_hook
        - image_prompt
        """
    fallback = {
        "email_subject": "[Fallback] Discover STM experiences",
        "email_body": (
            "STM helps people discover Thai-connected experiences across Europe and Bangkok. "
            "Explore festivals, markets, food experiences, wellness, and local cultural highlights."
        ),
        "social_caption": "Discover Thai-connected experiences across Europe and Bangkok with STM.",
        "cta": "Explore experiences",
        "ai_summary": "STM helps travelers and culture seekers discover Thai cultural events and curated Bangkok experiences.",
        "reel_hook": "Discover Thai-connected experiences with STM.",
        "image_prompt": "A modern editorial travel collage featuring Thai culture, Bangkok city life, markets, food, and European Thai events."
    }

    if evergreen:
        fallback["faq"] = [
            {
                "question": "What is STM?",
                "answer": "STM is a Thai culture and experience discovery platform connecting Europe and Bangkok."
            },
            {
                "question": "What can I find on STM?",
                "answer": "Thai events in Europe, Bangkok experiences, markets, food, festivals, wellness, and creative discovery."
            },
            {
                "question": "Who is STM for?",
                "answer": "Travelers, Thai culture seekers, and people moving between Europe and Thailand."
            }
        ]
        fallback["related_queries"] = [
            "thai events in europe",
            "bangkok experiences this week",
            "bangkok markets and pop ups",
            "thai culture bangkok guide",
            "bangkok 3 day itinerary"
        ]
        fallback["assets"] = {
            "pinterest": {
                "script": "Discover Thai-connected experiences across Europe and Bangkok with STM.",
                "hashtags": "#STM #ThaiCulture #BangkokGuide #ThaiEvents #ThailandTravel",
                "seo_title": "Discover Thai Culture and Bangkok Experiences",
                "seo_desc": "Explore Thai events in Europe and curated Bangkok experiences with STM.",
                "image_prompt": "A refined travel and culture collage showing Bangkok markets, Thai food, festivals, and Europe-based Thai events."
            },
            "blog": {
                "title": "Discover Thai Culture and Bangkok Experiences with STM",
                "script": "STM helps people discover Thai-connected experiences across Europe and Bangkok. This includes festivals, food, wellness, and curated local guides.",
                "seo_title": "Thai Culture and Bangkok Experiences Guide",
                "seo_desc": "Explore Thai cultural events in Europe and curated experiences in Bangkok.",
                "excerpt": "STM connects Thai culture, travel, and discovery across Europe and Bangkok."
            },
            "landing_page": {
                "hero_title": "Discover Thai-connected experiences",
                "hero_subtitle": "From Europe’s Thai events to Bangkok’s local discoveries",
                "intro": "STM helps you explore Thai culture, food, wellness, festivals, and curated local experiences across Europe and Bangkok.",
                "key_highlights": [
                    "Thai cultural events in Europe",
                    "Bangkok food and market experiences",
                    "Wellness and quiet discoveries",
                    "Travel-timed local guides"
                ]
            }
        }

    return chat_json(prompt, fallback)


