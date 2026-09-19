import os
import requests
import threading
from organisation_validator import validate_organisation
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ─── Step 1: Scrape website using Jina Reader ─────────────────────────────────
def scrape_website(website_url: str) -> dict:
    """Scrapes a website using Jina Reader API — completely free, no key needed."""
    if not website_url:
        return {"success": False, "text": "", "reason": "No website URL provided"}

    try:
        if not website_url.startswith("http"):
            website_url = f"https://{website_url}"

        jina_url = f"https://r.jina.ai/{website_url}"
        response = requests.get(jina_url, timeout=15, headers={
            "Accept": "text/plain",
            "X-Return-Format": "text"
        })

        if response.status_code == 200:
            text = response.text[:3000]
            return {"success": True, "text": text, "reason": None}
        else:
            return {
                "success": False,
                "text": "",
                "reason": f"Website returned status {response.status_code}"
            }
    except requests.exceptions.Timeout:
        return {"success": False, "text": "", "reason": "Website took too long to respond"}
    except Exception as e:
        return {"success": False, "text": "", "reason": str(e)}


# ─── Step 2: Build the AI prompt ─────────────────────────────────────────────
def build_prompt(entity_type: str, data: dict, website_text: str) -> str:
    """Builds the prompt for the AI based on registration data and scraped content."""

    if entity_type == "company":
        base_info = f"""
Organisation Type: Company
Company Name: {data.get('company_name', 'N/A')}
Industry: {data.get('industry_type', 'N/A')}
Region: {data.get('region', 'N/A')}
Address: {data.get('company_address', 'N/A')}
Contact Person: {data.get('contact_person', 'N/A')}
Website: {data.get('website', 'N/A')}
User-provided description: {data.get('description', 'N/A')}
"""
    else:
        base_info = f"""
Organisation Type: School
School Name: {data.get('school_name', 'N/A')}
Region: {data.get('region', 'N/A')}
Address: {data.get('school_address', 'N/A')}
Contact Person: {data.get('contact_person', 'N/A')}
Website: {data.get('website', 'N/A')}
User-provided description: {data.get('description', 'N/A')}
"""

    website_section = ""
    if website_text:
        website_section = f"""
Additional context scraped from the organisation's website:
{website_text}
"""

    prompt = f"""You are a professional profile writer.

Based on the following information, write a concise, factual, professional 
"About" description of this organisation in third person. The description should:
- Be 3 to 5 sentences long
- Describe who the organisation is, what they do, and where they operate
- Sound professional and warm
- Be written in a Ghanaian context
- Not mention internships, platforms, or partnerships
- Not include any headings, bullet points, or labels — just clean paragraph text

Organisation Information:
{base_info}
{website_section}

Write only the description. No preamble, no labels, no explanation."""

    return prompt


# ─── Step 3: Generate with Gemini ────────────────────────────────────────────
def generate_with_gemini(prompt: str) -> str:
    """Calls Google Gemini 3.5 Flash to generate the description."""
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        raise e


# ─── Step 4: Generate with Groq (fallback) ───────────────────────────────────
def generate_with_groq(prompt: str) -> str:
    """Calls Groq as fallback if Gemini fails."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq error: {e}")
        raise e


# ─── Step 5: Main generator function ─────────────────────────────────────────
def generate_description(entity_type: str, data: dict) -> dict:
    """
    Main function that orchestrates the full description generation pipeline.
    Returns a dict with the description, sources used, and confidence level.
    """
    sources_used = []
    sources_failed = []

    # ── Scrape website if provided ──
    website_result = {"success": False, "text": "", "reason": "Not attempted"}
    website = data.get("website", "")

    if website:
        scrape_result = scrape_website(website)
        if scrape_result["success"]:
            website_result = scrape_result
            sources_used.append("website_scrape")
            print(f"✅ Website scraped successfully")
        else:
            sources_failed.append(f"website_scrape: {scrape_result['reason']}")
            print(f"⚠️ Website scrape failed: {scrape_result['reason']}")
    else:
        sources_failed.append("website_scrape: No website provided")

    # Always count registration data as a source
    sources_used.append("registration_data")

    # ── Validate organisation existence before generating description ──
    validation = validate_organisation(
        entity_type,
        data,
        website_result.get("text", "")
    )

    if validation["action"] == "block":
        return {
            "success": False,
            "description": None,
            "sources_used": sources_used,
            "sources_failed": sources_failed,
            "confidence": "low",
            "ai_provider": None,
            "flagged": True,
            "flag_reason": validation["reason"],
            "flag_signals": validation["signals"],
            "action": "block",
            "error": "Organisation failed existence validation and was blocked"
        }

    if validation["action"] == "manual_review":
        # Still generate description but flag for admin awareness
        sources_failed.append(f"validation_warning: {validation['reason']}")
        print(f"Organisation flagged for manual review: {validation['reason']}")

    # ── Determine confidence level ──
    if len(sources_used) >= 2:
        confidence = "high"
    elif len(sources_used) == 1:
        confidence = "medium"
    else:
        confidence = "low"

    # ── Build the prompt ──
    prompt = build_prompt(
        entity_type,
        data,
        website_result.get("text", "")
    )

    # ── Try Gemini first, fall back to Groq ──
    ai_provider = None
    description = None

    try:
        description = generate_with_gemini(prompt)
        ai_provider = "gemini-3.5-flash"
        print(f"✅ Description generated with Gemini")
    except Exception:
        print(f"⚠️ Gemini failed, trying Groq...")
        try:
            description = generate_with_groq(prompt)
            ai_provider = "groq-gpt-oss-20b"
            print(f"✅ Description generated with Groq fallback")
        except Exception as e:
            print(f"❌ Both AI providers failed: {e}")
            description = None

    if not description:
        return {
            "success": False,
            "description": None,
            "sources_used": sources_used,
            "sources_failed": sources_failed,
            "confidence": "low",
            "ai_provider": None,
            "error": "Both AI providers failed to generate a description"
        }

    return {
        "success": True,
        "description": description,
        "sources_used": sources_used,
        "sources_failed": sources_failed,
        "confidence": confidence,
        "ai_provider": ai_provider,
        "flagged": validation["action"] == "manual_review",
        "flag_reason": validation["reason"] if validation["action"] == "manual_review" else None,
        "error": None
    }


# ─── Step 6: Background job runner ───────────────────────────────────────────
def generate_description_background(entity_type: str, entity_id: int,
                                     data: dict, save_callback):
    """
    Runs the description generation in a background thread so it does not
    block the registration response.
    """
    def run():
        print(f"🤖 Background AI description generation started for {entity_type} {entity_id}")
        result = generate_description(entity_type, data)
        if result["success"]:
            save_callback(entity_id, result["description"])
            print(f"Description saved for {entity_type} {entity_id} | "
                  f"Confidence: {result['confidence']} | "
                  f"Provider: {result['ai_provider']} | "
                  f"Sources: {result['sources_used']} | "
                  f"Flagged: {result.get('flagged', False)}")
        else:
            print(f"❌ Description generation failed for {entity_type} {entity_id}: "
                  f"{result['error']}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()