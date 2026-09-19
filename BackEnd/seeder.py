"""
ONE-TIME SEEDER SCRIPT
======================
Run this once after deployment to populate the verified_organisations table.
It scrapes SHSSelect (956 SHS schools) and BusinessGhana directory.

Usage:
    python seeder.py

Set your DB credentials in .env before running.
"""

import os
import time
import pymysql
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4"
}


# ─── Create table if it doesn't exist ────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS verified_organisations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    entity_type ENUM('company', 'school') NOT NULL,
    region VARCHAR(100),
    district VARCHAR(100),
    category VARCHAR(50),
    source_site VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name_type (name(100), entity_type),
    INDEX idx_entity_type (entity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def insert_organisation(cursor, name, entity_type, region, district, category, source_site):
    """Insert one organisation — skip if already exists."""
    try:
        cursor.execute("""
            INSERT IGNORE INTO verified_organisations 
            (name, entity_type, region, district, category, source_site)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, entity_type, region, district, category, source_site))
    except Exception as e:
        print(f"  Insert error for {name}: {e}")


# ─── Seeder 1: SHSSelect — All 956 SHS schools ───────────────────────────────
def seed_shs_schools(cursor):
    """
    Scrapes all SHS schools from shsselect.com/schools across all pages.
    Each page has 25 schools. ~39 pages total for 956 schools.
    """
    print("\n📚 Seeding SHS schools from SHSSelect...")
    total = 0
    page = 1

    while True:
        url = f"https://shsselect.com/schools?page={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"  Page {page} returned {response.status_code} — stopping")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Each school is a link with school details below it
            # Pattern from the fetched HTML: links with /schools/ path
            school_links = soup.find_all("a", href=lambda h: h and "/schools/" in h)

            if not school_links:
                print(f"  No more schools found on page {page} — done")
                break

            page_count = 0
            for link in school_links:
                text = link.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                if not lines:
                    continue

                school_name = lines[0]

                # Extract region from "Location: District, Region" pattern
                region = ""
                district = ""
                category = ""
                for line in lines:
                    if "Location:" in line:
                        loc = line.replace("Location:", "").strip()
                        parts = loc.split(",")
                        if len(parts) >= 2:
                            district = parts[0].strip()
                            region = parts[1].strip()
                    if "Category:" in line:
                        category = line.replace("Category:", "").strip()

                if school_name and len(school_name) > 2:
                    insert_organisation(
                        cursor, school_name, "school",
                        region, district, category, "shsselect.com"
                    )
                    page_count += 1
                    total += 1

            print(f"  Page {page}: {page_count} schools seeded")

            # Check if there's a next page
            next_link = soup.find("a", string=lambda t: t and "Next" in t)
            if not next_link:
                break

            page += 1
            time.sleep(1)  # Be polite to the server

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"✅ SHS schools seeded: {total} total")
    return total


# ─── Seeder 2: BusinessGhana — Company categories ────────────────────────────
def seed_companies_from_businessghana(cursor):
    """
    Scrapes company names from key BusinessGhana categories.
    Focuses on categories most relevant to student internships.
    """
    print("\n🏢 Seeding companies from BusinessGhana...")

    categories = [
        ("it", "Information Technology"),
        ("finance-companies", "Banking & Finance"),
        ("telecommunications", "Telecommunications"),
        ("health", "Healthcare"),
        ("media", "Media & Communications"),
        ("energy", "Oil & Gas"),
        ("engineering", "Engineering"),
        ("manufacturers", "Manufacturing / FMCG"),
        ("ngos", "NGO / Civil Society"),
        ("government", "Government / Public Sector"),
        ("education", "Education"),
    ]

    total = 0

    for cat_slug, industry in categories:
        url = f"https://www.businessghana.com/site/directory/{cat_slug}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"  Skipping {industry} — status {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # BusinessGhana directory items have links with company names
            company_links = soup.find_all("a", href=lambda h: h and "/site/directory/" in str(h))

            cat_count = 0
            for link in company_links:
                name = link.get_text(strip=True)
                # Filter out navigation links and short strings
                if name and len(name) > 3 and not any(
                    x in name.lower() for x in ["browse", "more", "add", "categories", "search"]
                ):
                    insert_organisation(
                        cursor, name, "company",
                        "", "", industry, "businessghana.com"
                    )
                    cat_count += 1
                    total += 1

            print(f"  {industry}: {cat_count} companies seeded")
            time.sleep(1)

        except Exception as e:
            print(f"  Error seeding {industry}: {e}")

    print(f"✅ Companies seeded: {total} total")
    return total


# ─── Main seeder runner ───────────────────────────────────────────────────────
def run_seeder():
    print("=" * 60)
    print("  CURIOUS MINDS — Verified Organisations Seeder")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    # Create table
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("✅ verified_organisations table ready")

    # Seed schools
    school_total = seed_shs_schools(cursor)
    conn.commit()

    # Seed companies
    company_total = seed_companies_from_businessghana(cursor)
    conn.commit()

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print(f"  Seeding complete!")
    print(f"  Schools seeded:   {school_total}")
    print(f"  Companies seeded: {company_total}")
    print(f"  Total:            {school_total + company_total}")
    print("=" * 60)


if __name__ == "__main__":
    run_seeder()