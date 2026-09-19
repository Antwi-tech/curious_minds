import os
import re
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DATABASE CHECK (Layer 1: Local DB)
# ═══════════════════════════════════════════════════════════════════════════════

def check_local_database(entity_type: str, name: str, db_connection) -> dict:
    if not db_connection:
        return {"found": False, "match_quality": "skipped", "source": "local_db", "details": None}

    try:
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT name, entity_type, region, source_site 
            FROM verified_organisations 
            WHERE LOWER(name) = LOWER(%s) AND entity_type = %s
            LIMIT 1
        """, (name.strip(), entity_type))
        result = cursor.fetchone()

        if result:
            return {
                "found": True,
                "match_quality": "exact",
                "source": "local_db",
                "details": {
                    "name": result[0],
                    "entity_type": result[1],
                    "region": result[2],
                    "source_site": result[3]
                }
            }

        cursor.execute("""
            SELECT name, entity_type, region, source_site 
            FROM verified_organisations 
            WHERE LOWER(name) LIKE LOWER(%s) AND entity_type = %s
            LIMIT 1
        """, (f"%{name.strip()}%", entity_type))
        result = cursor.fetchone()

        if result:
            return {
                "found": True,
                "match_quality": "partial",
                "source": "local_db",
                "details": {
                    "name": result[0],
                    "entity_type": result[1],
                    "region": result[2],
                    "source_site": result[3]
                }
            }

        return {"found": False, "match_quality": "not_found", "source": "local_db", "details": None}

    except Exception as e:
        print(f"Local DB check error: {e}")
        return {"found": False, "match_quality": "error", "source": "local_db", "details": None}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — LIVE SCRAPE CHECKS (Layer 2: External Sites)
# ═══════════════════════════════════════════════════════════════════════════════

def check_businessghana(company_name: str) -> dict:
    try:
        url = f"https://www.businessghana.com/site/items/search?search={requests.utils.quote(company_name)}"
        response = requests.get(url, headers=HEADERS, timeout=8)

        if response.status_code != 200:
            return {"found": False, "match_quality": "not_found", "source": "businessghana"}

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("a", class_="item-title")
        if not results:
            results = soup.find_all(["h3", "h4", "strong"])

        for result in results:
            result_text = result.get_text(strip=True).lower()
            if company_name.lower() in result_text or result_text in company_name.lower():
                return {
                    "found": True,
                    "match_quality": "exact" if result_text == company_name.lower() else "partial",
                    "source": "businessghana",
                    "matched_name": result.get_text(strip=True)
                }

        return {"found": False, "match_quality": "not_found", "source": "businessghana"}

    except requests.exceptions.Timeout:
        return {"found": False, "match_quality": "timeout", "source": "businessghana"}
    except Exception as e:
        print(f"BusinessGhana scrape error: {e}")
        return {"found": False, "match_quality": "error", "source": "businessghana"}


def check_gse(company_name: str) -> dict:
    try:
        url = "https://gse.com.gh/listed-companies/"
        response = requests.get(url, headers=HEADERS, timeout=8)

        if response.status_code != 200:
            return {"found": False, "match_quality": "not_found", "source": "gse"}

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(separator=" ", strip=True).lower()
        name_lower = company_name.lower()

        if name_lower in page_text:
            return {
                "found": True,
                "match_quality": "exact",
                "source": "gse",
                "note": "Listed on Ghana Stock Exchange — strong legitimacy signal"
            }

        first_word = name_lower.split()[0] if name_lower.split() else ""
        if len(first_word) > 3 and first_word in page_text:
            return {
                "found": True,
                "match_quality": "partial",
                "source": "gse",
                "note": "Partial match found on Ghana Stock Exchange"
            }

        return {"found": False, "match_quality": "not_found", "source": "gse"}

    except requests.exceptions.Timeout:
        return {"found": False, "match_quality": "timeout", "source": "gse"}
    except Exception as e:
        print(f"GSE scrape error: {e}")
        return {"found": False, "match_quality": "error", "source": "gse"}


def check_shsselect(school_name: str, region: str = "") -> dict:
    try:
        search_name = requests.utils.quote(school_name)
        url = f"https://shsselect.com/schools?search={search_name}"
        response = requests.get(url, headers=HEADERS, timeout=8)

        if response.status_code != 200:
            return {"found": False, "match_quality": "not_found", "source": "shsselect"}

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(separator=" ", strip=True).lower()
        name_lower = school_name.lower()

        if name_lower in page_text:
            region_match = region.lower() in page_text if region else False
            return {
                "found": True,
                "match_quality": "exact",
                "source": "shsselect",
                "region_confirmed": region_match
            }

        short_name = name_lower.replace("senior high school", "").replace(
            "senior high", "").replace("shs", "").strip()
        if len(short_name) > 3 and short_name in page_text:
            return {
                "found": True,
                "match_quality": "partial",
                "source": "shsselect",
                "region_confirmed": False
            }

        return {"found": False, "match_quality": "not_found", "source": "shsselect"}

    except requests.exceptions.Timeout:
        return {"found": False, "match_quality": "timeout", "source": "shsselect"}
    except Exception as e:
        print(f"SHSSelect scrape error: {e}")
        return {"found": False, "match_quality": "error", "source": "shsselect"}


def check_ghana_education_directory(school_name: str, school_type: str = "Junior High School") -> dict:
    try:
        category = "Junior%20High%20School" if "jhs" in school_type.lower() or "junior" in school_type.lower() else "Senior%20High%20School"
        url = f"http://ghanaeducationdirectory.com/Search/category?c={category}"
        response = requests.get(url, headers=HEADERS, timeout=8)

        if response.status_code != 200:
            return {"found": False, "match_quality": "not_found", "source": "ghana_edu_directory"}

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(separator=" ", strip=True).lower()
        name_lower = school_name.lower()

        if name_lower in page_text:
            return {"found": True, "match_quality": "exact", "source": "ghana_edu_directory"}

        short_name = name_lower.replace("junior high school", "").replace(
            "jhs", "").replace("senior high school", "").replace("shs", "").strip()
        if len(short_name) > 3 and short_name in page_text:
            return {"found": True, "match_quality": "partial", "source": "ghana_edu_directory"}

        return {"found": False, "match_quality": "not_found", "source": "ghana_edu_directory"}

    except requests.exceptions.Timeout:
        return {"found": False, "match_quality": "timeout", "source": "ghana_edu_directory"}
    except Exception as e:
        print(f"Ghana Education Directory error: {e}")
        return {"found": False, "match_quality": "error", "source": "ghana_edu_directory"}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_score(checks: dict, entity_type: str) -> dict:
    """
    Calculates the legitimacy score from all check results.

    Scoring weights:
    - AI validation high confidence:  +30 points  ← NEW
    - AI validation medium confidence: +15 points  ← NEW
    - AI validation negative:         -20 points  ← NEW
    - Local DB exact match:            30 points
    - Local DB partial match:          15 points
    - Live scrape exact match:         25 points (split across sources)
    - Live scrape partial match:       12 points
    - GSE listed bonus:               +25 points (strongest signal)
    - Email domain bonus:              +5 points
    - Website provided bonus:          +5 points
    - Free email penalty:             -10 points
    """
    score = 0
    signals = []

    # ── AI Validation result (from organisation_validator) ── NEW
    ai_validation = checks.get("ai_validation", {})
    if ai_validation.get("exists") and ai_validation.get("confidence") == "high":
        score += 30
        signals.append(
            f"✅ AI validation: organisation confirmed as real (high confidence) — "
            f"{ai_validation.get('reason', '')}"
        )
    elif ai_validation.get("exists") and ai_validation.get("confidence") == "medium":
        score += 15
        signals.append(
            f"⚠️ AI validation: organisation likely real (medium confidence) — "
            f"{ai_validation.get('reason', '')}"
        )
    elif ai_validation.get("exists") and ai_validation.get("confidence") == "low":
        score += 5
        signals.append(
            f"ℹ️ AI validation: organisation existence uncertain (low confidence) — "
            f"{ai_validation.get('reason', '')}"
        )
    elif not ai_validation.get("exists"):
        score -= 20
        signals.append(
            f"❌ AI validation: organisation could not be confirmed — "
            f"{ai_validation.get('reason', '')}"
        )

    # ── Local DB ──
    local = checks.get("local_db", {})
    if local.get("found"):
        if local.get("match_quality") == "exact":
            score += 30
            signals.append(
                f"✅ Found in local registry (exact match) — "
                f"source: {local.get('details', {}).get('source_site', 'registry')}"
            )
        else:
            score += 15
            signals.append(
                f"⚠️ Found in local registry (partial match) — "
                f"source: {local.get('details', {}).get('source_site', 'registry')}"
            )
    else:
        signals.append("❌ Not found in local registry database")

    # ── BusinessGhana (companies only) ──
    if entity_type == "company":
        bg = checks.get("businessghana", {})
        if bg.get("found"):
            if bg.get("match_quality") == "exact":
                score += 20
                signals.append("✅ Found on BusinessGhana directory (exact match)")
            else:
                score += 10
                signals.append("⚠️ Found on BusinessGhana directory (partial match)")
        else:
            signals.append("❌ Not found on BusinessGhana directory")

        # ── GSE (companies only) ──
        gse = checks.get("gse", {})
        if gse.get("found"):
            score += 25
            signals.append("✅ Listed on Ghana Stock Exchange — strong legitimacy signal")

    # ── SHSSelect (schools only) ──
    if entity_type == "school":
        shs = checks.get("shsselect", {})
        if shs.get("found"):
            if shs.get("match_quality") == "exact":
                score += 25
                signals.append("✅ Found on SHSSelect school directory (exact match)")
                if shs.get("region_confirmed"):
                    score += 5
                    signals.append("✅ Region also confirmed on SHSSelect")
            else:
                score += 12
                signals.append("⚠️ Found on SHSSelect school directory (partial match)")
        else:
            signals.append("❌ Not found on SHSSelect directory")

        # ── Ghana Education Directory (schools only) ──
        ged = checks.get("ghana_edu_directory", {})
        if ged.get("found"):
            if ged.get("match_quality") == "exact":
                score += 20
                signals.append("✅ Found on Ghana Education Directory (exact match)")
            else:
                score += 10
                signals.append("⚠️ Found on Ghana Education Directory (partial match)")
        else:
            signals.append("❌ Not found on Ghana Education Directory")

    # ── Email domain signals ──
    email_check = checks.get("email", {})
    free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "yahoo.co.uk"]
    email_domain = email_check.get("domain", "")

    if email_domain and email_domain not in free_providers:
        score += 5
        signals.append(f"✅ Professional email domain: @{email_domain}")
    elif email_domain in free_providers and checks.get("has_website"):
        score -= 10
        signals.append(
            f"⚠️ Free email provider ({email_domain}) used despite having a website — suspicious"
        )
    elif email_domain in free_providers:
        signals.append(
            f"ℹ️ Free email provider ({email_domain}) — acceptable for small organisations without a website"
        )

    # ── Website provided ──
    if checks.get("has_website"):
        score += 5
        signals.append("✅ Website URL provided")

    # Cap score at 100
    score = max(0, min(100, score))

    # Determine verdict
    if score >= 75:
        verdict = "high"
    elif score >= 50:
        verdict = "moderate"
    elif score >= 25:
        verdict = "low"
    else:
        verdict = "unverifiable"

    # Determine recommendation
    if score >= 85:
        recommendation = "recommend_approval"
    elif score >= 60:
        recommendation = "manual_review"
    elif score >= 30:
        recommendation = "needs_closer_review"
    else:
        recommendation = "recommend_rejection"

    return {
        "score": score,
        "verdict": verdict,
        "recommendation": recommendation,
        "signals": signals
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — AI SUMMARY GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_verification_summary(entity_type: str, name: str, score: int,
                                   verdict: str, signals: list,
                                   recommendation: str) -> str:
    signals_text = "\n".join(signals)

    prompt = f"""You are a verification analyst for Curious Minds, a Ghanaian educational platform.
    
An automated verification check has been completed for a {entity_type} that wants to join the platform.
Write a short 3-4 sentence plain-English summary of the findings for the platform admin.
End with one sentence recommendation. Be direct and factual. No jargon.

Organisation: {name}
Type: {entity_type}
Legitimacy Score: {score}/100
Verdict: {verdict}
Recommendation: {recommendation}

Check Results:
{signals_text}

Write only the summary. No labels or headings."""

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            # model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=200, temperature=0.3)
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini summary error: {e}")

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq summary error: {e}")
        return (f"{name} scored {score}/100 on automated verification checks. "
                f"Verdict: {verdict}. "
                f"The system recommendation is: {recommendation.replace('_', ' ')}. "
                f"Admin should review the signals above before making a final decision.")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — MAIN VERIFICATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def verify_organisation(entity_type: str, data: dict, db_connection=None) -> dict:
    import concurrent.futures
    from organisation_validator import validate_organisation as ai_validate

    # Extract fields
    if entity_type == "company":
        name = data.get("company_name", "")
        region = data.get("region", "")
        email = data.get("email", "")
        website = data.get("website", "")
    else:
        name = data.get("school_name", "")
        region = data.get("region", "")
        email = data.get("email", "")
        website = data.get("website", "")
        school_type = data.get("type", "SHS")

    email_domain = email.split("@")[-1].lower() if "@" in email else ""

    print(f"🔍 Starting verification for {entity_type}: {name}")

    all_checks = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:

        # Layer 1: Local DB
        local_future = executor.submit(
            check_local_database, entity_type, name, db_connection
        )

        # Layer 2: AI validation + live scrapes all in parallel
        ai_future = executor.submit(ai_validate, entity_type, data, "")

        if entity_type == "company":
            bg_future = executor.submit(check_businessghana, name)
            gse_future = executor.submit(check_gse, name)
        else:
            shs_future = executor.submit(check_shsselect, name, region)
            ged_future = executor.submit(
                check_ghana_education_directory, name,
                school_type if 'school_type' in locals() else "SHS"
            )

        # Collect all results
        all_checks["local_db"] = local_future.result()

        # ── AI validation result fed into scoring ── NEW
        ai_result = ai_future.result()
        all_checks["ai_validation"] = {
            "exists": ai_result.get("is_valid", True),
            "confidence": ai_result.get("confidence", "low"),
            "reason": ai_result.get("reason", "")
        }

        if entity_type == "company":
            all_checks["businessghana"] = bg_future.result()
            all_checks["gse"] = gse_future.result()
        else:
            all_checks["shsselect"] = shs_future.result()
            all_checks["ghana_edu_directory"] = ged_future.result()

    # Add email and website signals
    all_checks["email"] = {"domain": email_domain}
    all_checks["has_website"] = bool(website)

    # ── Calculate score ──
    scoring = calculate_score(all_checks, entity_type)

    print(f"📊 Score: {scoring['score']}/100 | Verdict: {scoring['verdict']} | "
          f"Recommendation: {scoring['recommendation']}")

    # ── Generate AI summary ──
    summary = generate_verification_summary(
        entity_type=entity_type,
        name=name,
        score=scoring["score"],
        verdict=scoring["verdict"],
        signals=scoring["signals"],
        recommendation=scoring["recommendation"]
    )

    return {
        "success": True,
        "entity_type": entity_type,
        "name": name,
        "legitimacy_score": scoring["score"],
        "verdict": scoring["verdict"],
        "recommendation": scoring["recommendation"],
        "signals": scoring["signals"],
        "summary": summary,
        "checks": {
            "local_db": all_checks["local_db"],
            "ai_validation": all_checks["ai_validation"],
            "live_scrape": {
                k: v for k, v in all_checks.items()
                if k not in ["local_db", "ai_validation", "email", "has_website"]
            }
        }
    }