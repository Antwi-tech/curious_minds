import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ─── Validation: Call AI to check if organisation is real ─────────────────────
def call_ai_for_validation(prompt: str) -> str:
    """Tries Gemini first, falls back to Groq for validation."""
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini validation error: {e}")

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2  # low temperature for consistent validation decisions
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq validation error: {e}")
        raise e


# ─── Validation: Parse AI JSON response safely ────────────────────────────────
def parse_validation_response(raw: str) -> dict:
    """
    Safely parses the AI's JSON validation response.
    Falls back to a default uncertain result if parsing fails.
    """
    try:
        # Strip markdown code fences if AI wraps response in ```json ... ```
        cleaned = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(cleaned)

        # Ensure all expected fields are present
        return {
            "exists": bool(result.get("exists", False)),
            "confidence": result.get("confidence", "low"),
            "reason": result.get("reason", "No reason provided"),
            "signals": result.get("signals", [])
        }
    except (json.JSONDecodeError, Exception) as e:
        print(f"Failed to parse validation response: {e}")
        print(f"Raw response was: {raw}")
        # If parsing fails, treat as uncertain — do not block registration
        return {
            "exists": True,
            "confidence": "low",
            "reason": "Validation response could not be parsed — flagged for manual review",
            "signals": []
        }


# ─── Validation: Build the validation prompt ─────────────────────────────────
def build_validation_prompt(entity_type: str, data: dict, website_text: str) -> str:
    """Builds the AI prompt for existence and legitimacy validation."""

    if entity_type == "company":
        name = data.get("company_name", "N/A")
        address = data.get("company_address", "N/A")
        industry = data.get("industry_type", "N/A")
    else:
        name = data.get("school_name", "N/A")
        address = data.get("school_address", "N/A")
        industry = "Educational Institution"

    email = data.get("email", "N/A")
    email_domain = data.get("email_domain", email.split("@")[-1] if "@" in email else "N/A")
    region = data.get("region", "N/A")
    website = data.get("website", "None provided")

    website_section = ""
    if website_text:
        website_section = f"""
Website content (scraped):
{website_text[:800]}
"""
    else:
        website_section = "Website content: Not available or not provided"

    prompt = f"""You are a validation assistant for Curious Minds, a Ghanaian digital platform.
Your job is to determine whether the following organisation is likely a real, 
legitimate {entity_type} operating in Ghana.

Evaluate based on these submitted details:

- Organisation Name: {name}
- Entity Type: {entity_type}
- Industry / Sector: {industry}
- Region: {region}
- Address: {address}
- Email: {email}
- Email Domain: {email_domain}
- Website: {website}

{website_section}

Apply the following checks in your evaluation:

1. NAME CHECK — Does the name look like a real organisation name?
   Flag if: random letters, gibberish, single generic word with no context, 
   or clearly not a Ghanaian organisation name.

2. WEBSITE CHECK — If website content is available, does it match the 
   submitted name, industry, and region? Flag if the content is completely 
   unrelated or belongs to a different organisation.

3. EMAIL DOMAIN CHECK — Is the email from a free provider (Gmail, Yahoo, 
   Hotmail, Outlook)? If yes and a website was also provided, flag as suspicious.
   A free email with no website is acceptable for small organisations.

4. INDUSTRY CONSISTENCY — Does the stated industry match what the website 
   content (if available) describes? Flag major mismatches.

5. REGION PLAUSIBILITY — Does the region field contain a valid Ghana region name?
   Flag if it contains a foreign country, city, or random text.

Based on all checks, respond ONLY in this exact JSON format with no extra text:
{{
    "exists": true or false,
    "confidence": "high" or "medium" or "low",
    "reason": "One clear sentence explaining your decision",
    "signals": [
        "signal 1 — what supported or raised concern",
        "signal 2 — what supported or raised concern"
    ]
}}

Rules for your decision:
- Return exists: false with confidence: high ONLY if you are very certain 
  the organisation is fake (e.g. gibberish name, website content is completely 
  unrelated, no matching signals at all)
- Return exists: true with confidence: low if you are unsure — this triggers 
  manual admin review rather than blocking the registration
- When in doubt, return exists: true — do not block legitimate organisations
- Do not assume an organisation is fake just because it is small or has no website
"""

    return prompt


# ─── Validation: Main validation function ────────────────────────────────────
def validate_organisation(entity_type: str, data: dict, website_text: str = "") -> dict:
    """
    Main validation function. Checks whether an organisation is likely real
    before allowing description generation to proceed.

    Returns:
        {
            "is_valid": True/False,
            "confidence": "high" / "medium" / "low",
            "reason": "explanation",
            "signals": ["signal 1", "signal 2"],
            "action": "proceed" / "manual_review" / "block"
        }
    """
    print(f"🔍 Running existence validation for {entity_type}...")

    try:
        prompt = build_validation_prompt(entity_type, data, website_text)
        raw_response = call_ai_for_validation(prompt)
        result = parse_validation_response(raw_response)

        exists = result["exists"]
        confidence = result["confidence"]

        # Determine action based on result
        if not exists and confidence == "high":
            # Very confident it's fake — block description generation
            action = "block"
        elif not exists and confidence in ("medium", "low"):
            # Uncertain — let admin review rather than blocking
            action = "manual_review"
        elif exists and confidence == "low":
            # Probably real but uncertain — flag for admin awareness
            action = "manual_review"
        else:
            # Confident it's real — proceed with description generation
            action = "proceed"

        print(f"Validation complete — exists: {exists}, "
              f"confidence: {confidence}, action: {action}")
        print(f"   Reason: {result['reason']}")

        return {
            "is_valid": exists,
            "confidence": confidence,
            "reason": result["reason"],
            "signals": result["signals"],
            "action": action
        }

    except Exception as e:
        print(f"Validation failed entirely: {e}")
        # If validation itself crashes, do not block — flag for manual review
        return {
            "is_valid": True,
            "confidence": "low",
            "reason": "Validation service unavailable — flagged for manual admin review",
            "signals": [],
            "action": "manual_review"
        }


# ─── How to integrate into ai_description_generator.py ───────────────────────
#
# At the top of ai_description_generator.py, add this import:
#
#   from organisation_validator import validate_organisation
#
# Then in your generate_description() function, after the website scrape
# and before the prompt is built, add this block:
#
#
 