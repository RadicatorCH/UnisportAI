"""Scrape Unisport offers, courses and course dates into Supabase.

This script extracts structured data from the public Unisport website and
persists it into Supabase across three conceptual tables:

- ``sportangebote``: offers (e.g. "Boxing", "TRX")
- ``sportkurse``: courses for an offer (with ``kursnr``, details, and a
    ``zeitraum_href`` linking to the course dates page)
- ``kurs_termine``: concrete scheduled sessions (``start_time``, ``end_time``,
    ``location_name``)

Workflow summary:
1. ``extract_offers`` reads the main index and returns a list of offers.
2. ``extract_courses_for_offer`` parses the course table for an offer.
3. ``extract_course_dates`` parses individual course date pages.
4. ``main`` orchestrates the extraction and upserts data idempotently.

The script is written to be idempotent: primary keys (``href``, ``kursnr``,
``(kursnr,start_time)``) are used during upserts to avoid duplicates.
"""

# Mini tutorial:
# - Step 1: Fetch offers from the main page (extract_offers)
# - Step 2: For each offer, read the courses (extract_courses_for_offer)
# - Step 3: For each course, read all dates (extract_course_dates)
# - Step 4: Write everything idempotently (upsert) into Supabase
#
# concept: Idempotency
# This script is designed so you can run it multiple times without creating duplicate entries.
# We use "upsert" (update or insert) operations. If a record with the same unique key
# (like a URL or course number) already exists, we update it; otherwise, we create it.

# Imports (beginner-friendly explanation of what we need them for in THIS script)
# Think of the imports as building blocks in Scratch – each one is good at a specific task.
# - os: To read environment variables (SUPABASE_URL/KEY) from the system/.env (our "settings")

import os
# - typing: For type hints (List, Dict) so the code is easier to understand

from typing import List, Dict, Optional
# - datetime: To convert date strings (e.g. 03.10.2025) into a machine-readable ISO format
from datetime import datetime
# - urllib.parse.urljoin: Turns relative links into full web addresses
from urllib.parse import urljoin, urlparse, parse_qs
# - re: "search with patterns" in texts (e.g. detect date/time)
import re
# - requests: Fetches web pages from the internet
import requests
# - bs4.BeautifulSoup: An "HTML magnifying glass" to find tables and cells
from bs4 import BeautifulSoup
# - supabase.create_client: Plug to the database (read/write)
from supabase import create_client
# - dotenv.load_dotenv: Reads the .env file (so keys don’t live in the code)
from dotenv import load_dotenv


def fetch_html(url: str) -> str:
    """Download HTML content for a URL.

    Uses a requests session with SSL warnings disabled and ``verify=False``
    to maximize robustness when fetching pages. The function raises on
    non-success HTTP responses.

    Args:
        url (str): URL or local file path to fetch.

    Returns:
        str: Raw HTML content.
    """
    # We disable SSL verification here because some university pages might have
    # certificate issues or strict firewalls. By using a browser-like User-Agent
    # and ignoring SSL errors, we ensure the script can read the page content.
    import ssl
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Work around SSL issues using disable_warnings and verify=False
    session = requests.Session()
    session.verify = False
    
    r = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    return r.text


def extract_offers(source: str) -> List[Dict[str, str]]:
    """Extract the list of offers from the main index page.

    The function accepts either a URL or a local file path. It looks for
    anchor elements under the selector ``dl.bs_menu dd a`` and returns a
    list of ``{"name": ..., "href": ...}`` dictionaries with absolute
    ``href`` values.

    Args:
        source (str): URL or path to the HTML file.

    Returns:
        List[Dict[str, str]]: Unique offers found on the page.
    """
    # List of offers that should be excluded
    excluded_offers = {
        "alle freien Kursplätze dieses Zeitraums",
    }
    
    if source.startswith("http://") or source.startswith("https://"):
        base_url = source
        html = fetch_html(source)
    else:
        base_url = ""
        with open(source, "r", encoding="utf-8") as f:
            html = f.read()
    soup = BeautifulSoup(html, "lxml")

    offers: List[Dict[str, str]] = []
    seen_hrefs = set()
    # "dl.bs_menu dd a" is a CSS selector that finds the links in the menu
    for a in soup.select("dl.bs_menu dd a"):
        name = a.get_text(strip=True)
        href = a.get("href")
        if not name or not href:
            continue
        
        # Skip excluded offers
        if name in excluded_offers:
            continue
            
        full_href = urljoin(base_url or "", href)
        if full_href in seen_hrefs:
            continue
        seen_hrefs.add(full_href)
        offers.append({"name": name, "href": full_href})
    return offers


def extract_courses_for_offer(offer: Dict[str, str]) -> List[Dict[str, str]]:
    """Parse the course table for a single offer page.

    Returns a list of course dictionaries containing at minimum ``kursnr``
    and a ``zeitraum_href`` when available. Temporary fields prefixed with
    ``_`` (e.g. ``_offer_name``) are included to assist later processing
    (trainer extraction, cancellation mapping) but are not persisted to DB.

    Args:
        offer (Dict[str, str]): Offer dict with keys ``name`` and ``href``.

    Returns:
        List[Dict[str, str]]: Courses parsed from the offer page.
    """
    href = offer["href"]
    name = offer["name"]
    if not (href.startswith("http://") or href.startswith("https://")):
        return []
    html = fetch_html(href)
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.bs_kurse")
    if not table:
        return []
    tbody = table.find("tbody") or table
    rows: List[Dict[str, str]] = []
    for tr in tbody.select("tr"):
        def text(sel: str) -> str:
            el = tr.select_one(sel)
            return el.get_text(" ", strip=True) if el else ""
        kursnr = text("td.bs_sknr")
        if not kursnr:
            continue
        details = text("td.bs_sdet")
        tag = text("td.bs_stag")
        zeit = text("td.bs_szeit")
        ort_cell = tr.select_one("td.bs_sort")
        # Location texts are no longer stored in sportkurse. Here we primarily need
        # location_name for kurs_termine (comes in extract_course_dates) and keep sportkurse s
        ort = ort_cell.get_text(" ", strip=True) if ort_cell else ""
        ort_link = ort_cell.select_one("a") if ort_cell else None
        ort_href = urljoin(href, ort_link.get("href")) if (ort_link and ort_link.get("href")) else None
        zr_cell = tr.select_one("td.bs_szr")
        zr_link = zr_cell.select_one("a") if zr_cell else None
        zeitraum_href = urljoin(href, zr_link.get("href")) if (zr_link and zr_link.get("href")) else None
        leitung = text("td.bs_skl")
        preis = text("td.bs_spreis")
        buch_cell = tr.select_one("td.bs_sbuch")
        buchung = buch_cell.get_text(" ", strip=True) if buch_cell else ""
        
        # Store temporary fields for trainer extraction (not written to the DB)
        # We use a naming convention where keys starting with "_" are for internal use only.
        course_data = {
            "offer_href": href,
            "kursnr": kursnr,
            "details": details,
            "zeitraum_href": zeitraum_href,
            "preis": preis,
            "buchung": buchung,
            # Temporary fields marked with _
            "_offer_name": name,  # needed for update_cancellations.py
            "_leitung": leitung,  # needed for trainer extraction
        }
        rows.append(course_data)
    return rows


def extract_offer_metadata(offer: Dict[str, str]) -> Dict[str, str]:
    """Extract image URL and description paragraphs for an offer page.

    The function tries to find a representative image (not logos/icons)
    near the page title and collects paragraph tags before the course
    table to form a description string.

    Args:
        offer (Dict[str, str]): Offer dict with ``href`` key.

    Returns:
        Dict[str, str]: May contain keys ``image_url`` and ``description``.
    """
    href = offer["href"]
    if not (href.startswith("http://") or href.startswith("https://")):
        return {}
    
    html = fetch_html(href)
    soup = BeautifulSoup(html, "lxml")
    
    result = {}
    
    # Find the element with the title (can be h1 or div.bs_head)
    title_element = soup.find("h1") or soup.find("div", class_="bs_head")
    if title_element:
        # After the title, we search for the first <img> tag
        # Start from the title and go through all siblings and their children
        img_tag = None
        current = title_element.find_next_sibling()
        
        while current and current.name != "table":
            # Check whether current itself is an img
            if current.name == "img":
                img_tag = current
                break
            # Check all children of this element
            if hasattr(current, 'find_all'):
                img = current.find("img")
                if img and img.get("src"):
                    img_src = img.get("src")
                    if "logo" not in img_src.lower() and "icon" not in img_src.lower():
                        img_tag = img
                        break
            current = current.find_next_sibling()
        
        if img_tag and img_tag.get("src"):
            img_src = img_tag.get("src")
            # Ignore logos and icons (often with "logo" or "icon" in src)
            if "logo" not in img_src.lower() and "icon" not in img_src.lower():
                # Convert relative URLs to absolute URLs
                result["image_url"] = urljoin(href, img_src)
    
    # find the table
    table = soup.select_one("table.bs_kurse")
    
    # Collect all <p> tags after the title
    paragraphs = []
    
    if title_element:
        # Find all <p> tags after the title element
        # Search in all following sibling elements
        current = title_element
        while current:
            current = current.next_sibling
            
            # When we reach a table, stop
            if current and hasattr(current, 'name') and current.name == "table":
                break
                
            # If current is a <p> tag, use it
            if current and hasattr(current, 'name') and current.name == "p":
                paragraphs.append(str(current))
            
            # If current has children, look for <p> tags in the children
            if current and hasattr(current, 'find_all'):
                for p in current.find_all("p"):
                    paragraphs.append(str(p))
    
    # Remove duplicates – keep the original order
    unique_paragraphs = []
    seen = set()
    for p in paragraphs:
        if p not in seen:
            unique_paragraphs.append(p)
            seen.add(p)
    
    if unique_paragraphs:
        result["description"] = "\n".join(unique_paragraphs)
    
    return result


def extract_trainer_names(leitung: str) -> List[str]:
    """Split a comma-separated trainers string into a list of names.

    Args:
        leitung (str): Comma-separated trainer names as presented on the site.

    Returns:
        List[str]: Cleaned trainer names.
    """
    if not leitung or not leitung.strip():
        return []
    
    # Split at commas and trim whitespace
    names = [name.strip() for name in leitung.split(",")]
    # Remove empty strings
    names = [name for name in names if name]
    return names


def parse_time_range(zeit_txt: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a human-readable time range into start/end ISO time strings.

    Supports formats like "16.10 - 17.40" or "16:10 - 17:40" and returns
    a tuple of (start_time, end_time) where each is a string like
    ``HH:MM:SS`` or ``None`` when parsing fails.

    Returns:
        tuple[Optional[str], Optional[str]]: (start_time, end_time)
    """
    if not zeit_txt or not zeit_txt.strip():
        return None, None
    
    # Replace period with colon for a consistent format
    zeit_normalized = zeit_txt.strip().replace(".", ":")
    
    # Try to parse different formats
    patterns = [
        r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})",  # 16:10 - 17:40
        r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2})\.(\d{2})",  # 16:10 - 17.40
        r"(\d{1,2})\.(\d{2})\s*-\s*(\d{1,2}):(\d{2})",  # 16.10 - 17:40
    ]
    
    for pattern in patterns:
        match = re.match(pattern, zeit_normalized)
        if match:
            h1, m1, h2, m2 = match.groups()
            start_hour = int(h1)
            start_min = int(m1)
            end_hour = int(h2)
            end_min = int(m2)
            return f"{start_hour:02d}:{start_min:02d}:00", f"{end_hour:02d}:{end_min:02d}:00"
    
    return None, None


def extract_course_dates(kursnr: str, zeitraum_href: str) -> List[Dict[str, str]]:
    """Parse the course dates page for a given ``kursnr``.

    Each table row represents a scheduled session. Dates are converted to
    ISO format (YYYY-MM-DD) and times are converted to ``HH:MM:SS``. The
    function returns a list of dictionaries suitable for upserting into
    the ``kurs_termine`` table.

    Args:
        kursnr (str): Course number identifier.
        zeitraum_href (str): URL to the course dates page.

    Returns:
        List[Dict[str, str]]: Parsed date records with keys like
            ``start_time``, ``end_time``, ``location_name``.
    """
    html = fetch_html(zeitraum_href)
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.bs_kurse")
    if not table:
        return []
    out: List[Dict[str, str]] = []
    for tr in table.select("tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        wochentag = tds[0].get_text(" ", strip=True)
        datum_raw = tds[1].get_text(" ", strip=True)
        zeit_txt = tds[2].get_text(" ", strip=True)
        ort_cell = tds[3]
        ort_txt = ort_cell.get_text(" ", strip=True)
        a = ort_cell.find("a")
        ort_href = urljoin(zeitraum_href, a.get("href")) if (a and a.get("href")) else None
        try:
            datum_iso = datetime.strptime(datum_raw, "%d.%m.%Y").date().isoformat()
        except Exception:
            continue
        
        # Parse time into start_time and end_time
        start_time, end_time = parse_time_range(zeit_txt)
        
        location_name = ort_txt.strip() or None
        
        # Combine date with start_time/end_time to create a timestamp
        # If no time can be parsed, we skip this entry
        if not start_time:
            print(f"⚠️  Could not parse time for {kursnr} on {datum_iso}: '{zeit_txt}' - skipping entry")
            continue
        
        start_timestamp = f"{datum_iso}T{start_time}"
        end_timestamp = f"{datum_iso}T{end_time}" if end_time else None
        
        out.append({
            "kursnr": kursnr,
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "ort_href": ort_href,
            "location_name": location_name,
        })
    return out


def main() -> None:
    # 1) Load environment variables from .env (if present).
    #    This keeps credentials out of source control.
    load_dotenv()
    # 2) Use the live offers index page as the canonical source
    html_source = "https://www.sportprogramm.unisg.ch/unisg/angebote/aktueller_zeitraum/index.html"
    offers = extract_offers(html_source)  # list of {name, href}

    # 3) Connect to Supabase using environment credentials
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Please set SUPABASE_URL and SUPABASE_KEY in the environment.")
        return
    supabase = create_client(supabase_url, supabase_key)  # DB connection

    # 4) First, we write the offers into the "sportangebote" table.
    #    Upsert means: if an entry already exists (same key), it will be updated.
    #    The key here is the "href" column (the link to the offer page).
    # Idempotent: same href → will be updated instead of duplicated
    supabase.table("sportangebote").upsert(offers, on_conflict="href").execute()
    print(f"Supabase: {len(offers)} offers upserted (idempotent).")

    # 4b) Extract image URL and description text from each offer page
    #     and update the entries in the database
    updated_count = 0
    for offer in offers:
        metadata = extract_offer_metadata(offer)
        if metadata:
            # Prepare update: href + name + new fields
            update_data = {
                "href": offer["href"],
                "name": offer["name"]
            }
            if "image_url" in metadata:
                update_data["image_url"] = metadata["image_url"]
            if "description" in metadata:
                update_data["description"] = metadata["description"]
            # Upsert with the new fields
            supabase.table("sportangebote").upsert(update_data, on_conflict="href").execute()
            updated_count += 1
    print(f"Supabase: Image URL and descriptions updated for {updated_count} offers.")

    # 5) Next, we collect all courses for all offers.
    #    For this, we visit the detail page of each offer and read the course table.
    all_courses: List[Dict[str, str]] = []
    for off in offers:  # visit each offer page
        all_courses.extend(extract_courses_for_offer(off))
    #    Then we write all courses into the "sportkurse" table.
    #    The key is the course number ("kursnr").
    # Clean up temporary fields (_leitung) before the upsert
    courses_for_db = [
        {k: v for k, v in course.items() if not k.startswith("_")}
        for course in all_courses
    ]
    
    # Idempotent: same kursnr → will be updated
    supabase.table("sportkurse").upsert(courses_for_db, on_conflict="kursnr").execute()
    print(f"Supabase: {len(courses_for_db)} courses upserted (idempotent).")

    # 5b) Extract trainer names from all courses and store them
    trainer_to_courses: Dict[str, List[str]] = {}  # trainer_name -> [kursnr, kursnr, ...]
    
    for course in all_courses:
        leitung = course.get("_leitung", "").strip() if course.get("_leitung") else ""
        if leitung:
            trainer_names = extract_trainer_names(leitung)
            for trainer_name in trainer_names:
                # Track which courses each trainer teaches
                if trainer_name not in trainer_to_courses:
                    trainer_to_courses[trainer_name] = []
                trainer_to_courses[trainer_name].append(course["kursnr"])
    
    # Deduplicate trainer list (trainer_name -> rating dict)
    all_trainers: List[Dict[str, object]] = [
        {"name": trainer_name, "rating": 3}
        for trainer_name in trainer_to_courses.keys()
    ]
    
    # Save trainers into the trainer table (idempotent)
    if all_trainers:
        supabase.table("trainer").upsert(all_trainers, on_conflict="name").execute()
        print(f"Supabase: {len(all_trainers)} trainers upserted (idempotent).")
    
    # Save relationships in the kurs_trainer table
    kurs_trainer_rows: List[Dict[str, object]] = []
    for trainer_name, kursnrs in trainer_to_courses.items():
        for kursnr in kursnrs:
            kurs_trainer_rows.append({"kursnr": kursnr, "trainer_name": trainer_name})
    
    if kurs_trainer_rows:
        # Delete existing relationships for these courses first to avoid duplicates
        kursnrs_to_update = [course["kursnr"] for course in all_courses]
        for kursnr in kursnrs_to_update:
            supabase.table("kurs_trainer").delete().eq("kursnr", kursnr).execute()
        # Insert new relationships
        supabase.table("kurs_trainer").insert(kurs_trainer_rows).execute()
        print(f"Supabase: {len(kurs_trainer_rows)} course-trainer relationships saved.")

    # 6) Now we handle the exact dates for each course.
    #    For each course there is a link (zeitraum_href) to a subpage with all scheduled dates.
    all_dates: List[Dict[str, str]] = []
    for c in all_courses:  # visit dates page per course
        if c.get("zeitraum_href") and c.get("kursnr"):
            all_dates.extend(extract_course_dates(c["kursnr"], c["zeitraum_href"]))
        # Delete existing relationships for these courses first to avoid duplicates
    if all_dates:
        # Before upsert: clean invalid location_name (set to NULL if not in unisport_locations)
        loc_resp = supabase.table("unisport_locations").select("name").execute()  # fetch allowed locations
        valid_names = { (r.get("name") or "").strip() for r in (loc_resp.data or []) if r.get("name") }
        for row in all_dates:
            ln = (row.get("location_name") or "").strip()
            if not ln or (valid_names and ln not in valid_names):
                row["location_name"] = None
        # MERGE strategy: the canceled flag is NOT overwritten, only set if it is not already set
        # Load existing canceled status for all dates in a single query
        kursnrs_with_dates = [(row["kursnr"], row["start_time"]) for row in all_dates]
        existing_canceled = {}
        
    #    We write these dates back into "kurs_termine" (legacy table), now with a location_name link.
        if kursnrs_with_dates:
            # Fetch all existing canceled values
            kursnrs_set = set(kr[0] for kr in kursnrs_with_dates)
            for kursnr in kursnrs_set:
                resp = supabase.table("kurs_termine").select("kursnr, start_time, canceled").eq("kursnr", kursnr).execute()
                for term in resp.data or []:
                    existing_canceled[(term["kursnr"], term["start_time"])] = term.get("canceled", False)
        
        # Set canceled only if it does not already exist
        for row in all_dates:
            key = (row["kursnr"], row["start_time"])
            if key in existing_canceled:
                # Keep the existing canceled status
                row["canceled"] = existing_canceled[key]
            else:
                # New date, canceled = false
                row["canceled"] = False
        
        supabase.table("kurs_termine").upsert(all_dates, on_conflict="kursnr,start_time").execute()  # Idempotent per (kursnr, start_time)
        print(f"Supabase: {len(all_dates)} dates upserted (kurs_termine, idempotent, keeping canceled status).")
    else:
        print("Note: No dates found.")

    # Log ETL run
    try:
        supabase.table("etl_runs").insert({"component": "scrape_sportangebote"}).execute()
    except Exception:
        pass

    # Note: The logic for detecting and marking training cancellations
    #       has been moved to update_cancellations.py so that both
    #       scripts can run independently.

if __name__ == "__main__":
    main()

# Note (Academic Integrity): The tool "Cursor" was used as a supporting aid
# in the creation of this file.
