"""
TEST SCRIPT — Curious Minds Verification Assistant
===================================================
Run this from your backend folder to test both company and school verification.

Usage:
    python test_verification.py
"""

from verification_assistant import verify_organisation
import json


# ─── Test 1: Real company ─────────────────────────────────────────────────────
def test_real_company():
    print("\n" + "="*60)
    print("TEST 1: Real Company — MTN Ghana")
    print("="*60)

    data = {
        "company_name": "MTN Ghana",
        "region": "Greater Accra",
        "company_address": "Independence Avenue, Accra",
        "email": "info@mtn.com.gh",
        "website": "https://www.mtn.com.gh",
        "industry_type": "Telecommunications"
    }

    result = verify_organisation("company", data, db_connection=None)
    print_result(result)


# ─── Test 2: Real school ──────────────────────────────────────────────────────
def test_real_school():
    print("\n" + "="*60)
    print("TEST 2: Real School — Achimota Senior High")
    print("="*60)

    data = {
        "school_name": "Achimota Senior High",
        "region": "Greater Accra",
        "school_address": "Achimota, Accra",
        "email": "admin@achimota.edu.gh",
        "website": "https://www.achimotas.edu.gh",
        "type": "SHS"
    }

    result = verify_organisation("school", data, db_connection=None)
    print_result(result)


# ─── Test 3: Fake/gibberish company ──────────────────────────────────────────
def test_fake_company():
    print("\n" + "="*60)
    print("TEST 3: Fake Company — asdfgh xyz ltd")
    print("="*60)

    data = {
        "company_name": "asdfgh xyz ltd",
        "region": "Greater Accra",
        "company_address": "some address",
        "email": "fake@gmail.com",
        "website": "",
        "industry_type": "Information Technology"
    }

    result = verify_organisation("company", data, db_connection=None)
    print_result(result)


# ─── Test 4: Real company with Gmail (suspicious) ─────────────────────────────
def test_suspicious_company():
    print("\n" + "="*60)
    print("TEST 4: Suspicious — Ecobank Ghana with Gmail")
    print("="*60)

    data = {
        "company_name": "Ecobank Ghana",
        "region": "Greater Accra",
        "company_address": "19 Seventh Avenue, Ridge West, Accra",
        "email": "ecobank@gmail.com",
        "website": "https://www.ecobank.com",
        "industry_type": "Banking & Finance"
    }

    result = verify_organisation("company", data, db_connection=None)
    print_result(result)


# ─── Test 5: GSE listed company ───────────────────────────────────────────────
def test_gse_company():
    print("\n" + "="*60)
    print("TEST 5: GSE Listed — Ghana Commercial Bank")
    print("="*60)

    data = {
        "company_name": "GCB Bank",
        "region": "Greater Accra",
        "company_address": "Thorpe Road, Accra",
        "email": "info@gcbbank.com.gh",
        "website": "https://www.gcbbank.com.gh",
        "industry_type": "Banking & Finance"
    }

    result = verify_organisation("company", data, db_connection=None)
    print_result(result)


# ─── Print result helper ──────────────────────────────────────────────────────
def print_result(result):
    print(f"\n  Name:            {result['name']}")
    print(f"  Score:           {result['legitimacy_score']}/100")
    print(f"  Verdict:         {result['verdict'].upper()}")
    print(f"  Recommendation:  {result['recommendation']}")
    print(f"\n  Signals:")
    for signal in result['signals']:
        print(f"    {signal}")
    print(f"\n  AI Summary:")
    print(f"    {result['summary']}")
    print(f"\n  Check Details:")
    print(f"    Local DB:    {result['checks']['local_db']['match_quality']}")
    for source, check in result['checks']['live_scrape'].items():
        print(f"    {source}: {check.get('match_quality', 'N/A')}")


# ─── Run all tests ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🔍 CURIOUS MINDS — Verification Assistant Test Suite")
    print("Running without local DB (db_connection=None)")
    print("Only live scrape checks will run\n")

    test_real_company()
    test_real_school()
    test_fake_company()
    test_suspicious_company()
    test_gse_company()

    print("\n\n✅ All tests complete")