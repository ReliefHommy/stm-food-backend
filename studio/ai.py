import os
import json
from openai import OpenAI
from django.conf import settings

def get_client():
    api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def gen_auto_post(language, topic, keywords, tone):
    client = get_client()
    prompt = f"""
    Write a social media caption and 8-12 hashtags in {language}.
    Topic: {topic}
    Keywords: {keywords}
    Tone: {tone}
    Return JSON with keys: caption, hashtags (comma separated), image_prompt (for Canva).
    """
    rsp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        response_format={"type":"json_object"}
    )
    return rsp.choices[0].message.content

def gen_review_reply(language, tone, review_text):
    client = get_client()
    prompt = f"""
    Write a culturally appropriate, polite reply in {language}.
    Tone: {tone}
    Customer review: {review_text}
    Keep it under 120 words.
    """
    rsp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    return rsp.choices[0].message.content.strip()

def gen_campaign(language, keywords, goal, evergreen=False):
    """
    Backward-compatible:
    - Still returns a JSON string.
    - Still includes top-level: email_subject, email_body, social_caption, cta
    Evergreen mode (evergreen=True):
    - Also returns structured assets for Pinterest and Blog under `assets`.
    - Adds seo_title/seo_desc and image_prompt.
    """

    client = get_client()

    if evergreen:
        prompt = f"""
        You are a marketing assistant for Somtam marketplace.. 
        Create an evergreen campaign in {language} based on.
        Goal: {goal}
        Keywords/context: {keywords}

        Return JSON with BOTH:
        1) Backward -compat keys:
        - email_subject
        - email_body (150-220 words)
        - social_caption (= 120 words)

        2) Evergreen structured assets:
        "assets": {{
             "pinterest": {{
               "script": "2-3 sentence caption in {language}",
               "hashtags": "8-12 hashtags, comma separated",
               "seo_title": "<=70 chars",
               "seo_desc": "<=160 chars",
               "image_prompt": "clear visual prompt for food/scene"
             }},
             "blog": {{
               "script": "350-600 words, H2/H3 sections, bullets where helpful",
               "seo_title": "<=70 chars",
               "seo_desc": "<=160 chars"
             }}
           }}
        

            Ensure valid JSON only.
            """
    else:
        prompt = f"""
        You are a marketing assistant for Somtam marketplace.. 
        Create a campaign in {language} based on.
        Goal: {goal}
        Keywords/context: {keywords}

        Return JSON with keys:
        - email_subject
        - email_body (150-220 words)
        - social_caption (= 120 words)
        - cta (call to action)
        """
    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"}
        )
        return rsp.choices[0].message.content
    except Exception as e:
        # Friendly fallback that won't crash your view
        fallback = {
            "email_subject": "[Fallback] Campaign coming soon",
            "email_body": (
                "Our AI quota is currently unavailable. Here’s a placeholder text. "
                "Please retry generation in a few minutes or contact the admin."
            ),
            "social_caption": "We’re preparing something tasty—stay tuned! 🍜",
            "cta": "Explore our latest products",
        }
        if evergreen:
            fallback["assets"] = {
                "pinterest": {
                    "script": "Delicious food is on the way! Stay tuned for more updates.",
                    "hashtags": "#food #delicious #staytuned",
                    "seo_title": "Exciting Food Updates Coming Soon",
                    "seo_desc": "Stay tuned for delicious food updates from Somtam marketplace.",
                    "image_prompt": "A vibrant and appetizing dish of Somtam salad with fresh ingredients."
                },
                "blog": {
                    "script": (
                        "We are excited to announce that new and delicious food content is coming soon. "
                        "Stay tuned for updates and explore our offerings!"
                    ),
                    "seo_title": "New Food Content Coming Soon",
                    "seo_desc": "Stay updated with the latest delicious food content from Somtam marketplace."
                }
            }
        return json.dumps(fallback)


