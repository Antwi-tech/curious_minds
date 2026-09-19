"""
Loop through pages by number instead of looking for a Next button.
SHSSelect has ~39 pages of 25 schools each = 956 schools total.
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


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def insert_organisation(cursor, name, entity_type, region, district, category, source_site):
    try:
        cursor.execute("""
            INSERT IGNORE INTO verified_organisations 
            (name, entity_type, region, district, category, source_site)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, entity_type, region, district, category, source_site))
    except Exception as e:
        print(f"  Insert error for {name}: {e}")


def seed_shs_schools_fixed(cursor):
    """
    Fixed version — loops through page numbers directly.
    Stops when a page returns 0 schools instead of looking for Next button.
    Max 50 pages as a safety cap (956 schools / 25 per page = ~39 pages).
    """
    print("\n📚 Seeding SHS schools from SHSSelect (fixed)...")
    total = 0
    consecutive_empty = 0

    for page in range(1, 51):  # max 50 pages
        url = f"https://shsselect.com/schools?page={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code == 403:
                print(f"  Page {page}: blocked (403) — trying alternate URL format")
                # Try without query param
                url = f"https://shsselect.com/schools/{page}"
                response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code != 200:
                print(f"  Page {page}: status {response.status_code} — stopping")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Try multiple selectors to find school links
            school_links = (
                soup.find_all("a", href=lambda h: h and "/schools/" in str(h)) or
                soup.find_all("h2") or
                soup.find_all("h3") or
                soup.find_all("div", class_=lambda c: c and "school" in str(c).lower())
            )

            if not school_links:
                consecutive_empty += 1
                print(f"  Page {page}: no schools found")
                if consecutive_empty >= 2:
                    print("  Two consecutive empty pages — seeding complete")
                    break
                continue

            consecutive_empty = 0
            page_count = 0

            for link in school_links:
                text = link.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                if not lines:
                    continue

                school_name = lines[0]
                region = ""
                district = ""
                category = ""

                for line in lines:
                    if "Location:" in line:
                        loc = line.replace("Location:", "").strip()
                        parts = loc.split(",")
                        if len(parts) >= 2:
                            district = parts[0].strip()
                            region = parts[-1].strip()
                    if "Category:" in line or "Type:" in line:
                        category = line.split(":")[-1].strip()

                if school_name and len(school_name) > 2:
                    insert_organisation(
                        cursor, school_name, "school",
                        region, district, category or "SHS", "shsselect.com"
                    )
                    page_count += 1
                    total += 1

            print(f"  Page {page}: {page_count} schools seeded (running total: {total})")
            time.sleep(1.5)  # polite delay between requests

        except requests.exceptions.Timeout:
            print(f"  Page {page}: timeout — skipping")
            continue
        except Exception as e:
            print(f"  Page {page}: error — {e}")
            break

    print(f"✅ SHS schools seeded: {total} total")
    return total


def seed_wikipedia_shs(cursor):
    """
    Fallback: seed SHS schools from Wikipedia list.
    Wikipedia has a clean, reliable list of Ghana SHS schools.
    No pagination — all on one page.
    """
    print("\n📚 Seeding SHS schools from Wikipedia (fallback)...")
    total = 0

    try:
        url = "https://en.wikipedia.org/wiki/List_of_senior_high_schools_in_Ghana"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            print(f"  Wikipedia returned {response.status_code}")
            return 0

        soup = BeautifulSoup(response.text, "html.parser")

        # Wikipedia SHS list is in tables
        tables = soup.find_all("table", class_="wikitable")
        print(f"  Found {len(tables)} tables")

        for table in tables:
            rows = table.find_all("tr")[1:]  # skip header row
            for row in rows:
                cols = row.find_all(["td", "th"])
                if not cols:
                    continue

                school_name = cols[0].get_text(strip=True)

                # Extract region if available (usually column 2 or 3)
                region = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                district = cols[2].get_text(strip=True) if len(cols) > 2 else ""

                # Clean up name
                school_name = school_name.replace("[1]", "").replace("[2]", "").strip()

                if school_name and len(school_name) > 3:
                    insert_organisation(
                        cursor, school_name, "school",
                        region, district, "SHS", "wikipedia"
                    )
                    total += 1

        print(f"✅ Wikipedia SHS schools seeded: {total} total")
        return total

    except Exception as e:
        print(f"  Wikipedia seeder error: {e}")
        return 0


# ─── Run fixed seeder ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  CURIOUS MINDS — Fixed School Seeder")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    # Try SHSSelect first
    total = seed_shs_schools_fixed(cursor)
    conn.commit()

    # If SHSSelect gave very few results, supplement with Wikipedia
    if total < 100:
        print(f"\n⚠️  Only {total} schools from SHSSelect — supplementing with Wikipedia...")
        wiki_total = seed_wikipedia_shs(cursor)
        conn.commit()
        total += wiki_total

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print(f"  School seeding complete — {total} schools total")
    print("=" * 60)