import os
import json
import logging
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# OpenAI Client
# ---------------------------------------------------------

def get_client():
    api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    return OpenAI(api_key=api_key)


# ---------------------------------------------------------
# AI Model
# ---------------------------------------------------------

AI_MODEL = getattr(
    settings,
    "OPENAI_CONTENT_MODEL",
    os.getenv("OPENAI_CONTENT_MODEL", "gpt-5.6-luna")
)


# ---------------------------------------------------------
# Generic AI Generator
# ---------------------------------------------------------

def generate_ai(prompt, json_mode=False):
    client = get_client()

    try:
        if json_mode:
            response = client.responses.create(
                model=AI_MODEL,
                input=prompt,
                reasoning={"effort": "none"},
                text={
                    "format": {
                        "type": "json_object"
                    }
                }
            )

            if not response.output_text:
                raise RuntimeError("AI generation returned empty output_text")

            return response.output_text

        else:
            response = client.responses.create(
                model=AI_MODEL,
                input=prompt,
                reasoning={"effort": "none"}
            )

            if not response.output_text:
                raise RuntimeError("AI generation returned empty output_text")

            return response.output_text.strip()

    except Exception as e:
        raise RuntimeError(f"AI generation failed: {str(e)}")


# ---------------------------------------------------------
# Auto Social Post
# ---------------------------------------------------------

def gen_auto_post(language, topic, keywords, tone):

    prompt = f"""
You are a social media content creator.

Write a social media caption and 8-12 relevant hashtags.

Language: {language}
Topic: {topic}
Keywords: {keywords}
Tone: {tone}

Return JSON with exactly these keys:

{{
    "caption": "...",
    "hashtags": "hashtag1, hashtag2, hashtag3",
    "image_prompt": "..."
}}
"""

    return generate_ai(prompt, json_mode=True)


# ---------------------------------------------------------
# Review Reply
# ---------------------------------------------------------

def gen_review_reply(language, tone, review_text):

    prompt = f"""
Write a culturally appropriate and polite customer review reply.

Language: {language}
Tone: {tone}

Customer review:
{review_text}

Keep the reply under 120 words.
"""

    return generate_ai(prompt)


# ---------------------------------------------------------
# Campaign Generator
# ---------------------------------------------------------

def gen_campaign(language, keywords, goal, evergreen=False):

    if evergreen:

        prompt = f"""
You are a content strategist for STM, a Thai culture,
food and experience discovery platform connecting Europe and Bangkok.

Create an evergreen marketing campaign.

Language: {language}
Goal: {goal}
Keywords/context: {keywords}

Return JSON with these keys:

{{
    "email_subject": "...",
    "email_body": "150-220 words",
    "social_caption": "approximately 120 words",
    "cta": "...",

    "assets": {{
        "pinterest": {{
            "script": "2-3 sentences",
            "hashtags": "8-12 hashtags, comma separated",
            "seo_title": "maximum 70 characters",
            "seo_desc": "maximum 160 characters",
            "image_prompt": "clear visual prompt"
        }},

        "blog": {{
            "script": "350-600 words with H2/H3 sections",
            "seo_title": "maximum 70 characters",
            "seo_desc": "maximum 160 characters"
        }}
    }}
}}
"""

    else:

        prompt = f"""
You are a marketing assistant for Somtam Market.

Create a marketing campaign.

Language: {language}
Goal: {goal}
Keywords/context: {keywords}

Return JSON with exactly these keys:

{{
    "email_subject": "...",
    "email_body": "150-220 words",
    "social_caption": "approximately 120 words",
    "cta": "..."
}}
"""

    try:
        return generate_ai(prompt, json_mode=True)

    except Exception:
        logger.exception("gen_campaign AI generation failed (evergreen=%s)", evergreen)

        fallback = {
            "email_subject": "[Fallback] Campaign coming soon",
            "email_body": (
                "Our AI service is temporarily unavailable. "
                "Please retry generation in a few minutes."
            ),
            "social_caption": (
                "We're preparing something tasty—stay tuned! 🍜"
            ),
            "cta": "Explore our latest products",
        }

        if evergreen:

            fallback["assets"] = {
                "pinterest": {
                    "script": "Delicious food is on the way!",
                    "hashtags": "#food #delicious #thailand",
                    "seo_title": "Thai Food and Culture",
                    "seo_desc": "Discover Thai food, culture and experiences.",
                    "image_prompt": (
                        "A vibrant Thai food scene with fresh ingredients."
                    )
                },
                "blog": {
                    "script": (
                        "Discover Thai food, culture and experiences "
                        "through STM."
                    ),
                    "seo_title": "Discover Thai Food and Culture",
                    "seo_desc": (
                        "Explore Thai food, culture and experiences with STM."
                    )
                }
            }

        return json.dumps(fallback, ensure_ascii=False)


