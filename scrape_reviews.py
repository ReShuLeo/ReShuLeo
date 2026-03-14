#!/usr/bin/env python3
"""
Scraper for cooking class reviews from northern Italian lakes.
Targets: Lake Como (priority), Lake Garda, Lake Maggiore, Lake Iseo, Tuscany.
Output: reviews_database.csv + reviews_database.json
"""

import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ── Playwright (optional, for JS-heavy sites) ─────────────────────────────────
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    # Auto-install system dependencies if missing (needed on Colab/Docker)
    import subprocess as _sp
    _result = _sp.run(["playwright", "install-deps", "chromium"],
                      capture_output=True, text=True)
    if _result.returncode != 0:
        print("⚠  playwright install-deps failed (may need root):", _result.stderr[:200])
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠  Playwright not installed – JS-heavy sources will be skipped.")

# ── langdetect (optional) ─────────────────────────────────────────────────────
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraping_errors.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PROGRESS_LOG = "scraping_progress.log"

# ─────────────────────────────────────────────────────────────────────────────
# Constants & config
# ─────────────────────────────────────────────────────────────────────────────
CSV_FILE = "reviews_database.csv"
JSON_FILE = "reviews_database.json"
SAVE_EVERY = 50  # save intermediate results every N new reviews

CSV_COLUMNS = [
    "id", "platform", "region", "city", "host_name",
    "reviewer_name", "reviewer_location", "reviewer_country",
    "language", "rating", "date", "occasion", "review_text", "url",
]

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# City → country mapping (expanded)
CITY_TO_COUNTRY: dict[str, str] = {
    # USA
    "new york": "USA", "los angeles": "USA", "chicago": "USA",
    "san diego": "USA", "boston": "USA", "san francisco": "USA",
    "houston": "USA", "phoenix": "USA", "philadelphia": "USA",
    "dallas": "USA", "seattle": "USA", "denver": "USA",
    "atlanta": "USA", "miami": "USA", "minneapolis": "USA",
    "portland": "USA", "nashville": "USA", "charlotte": "USA",
    "austin": "USA", "las vegas": "USA", "washington": "USA",
    "dc": "USA", "new orleans": "USA", "kansas city": "USA",
    "pittsburgh": "USA", "cleveland": "USA", "baltimore": "USA",
    "columbus": "USA", "indianapolis": "USA", "memphis": "USA",
    "connecticut": "USA", "texas": "USA", "california": "USA",
    "florida": "USA", "new jersey": "USA", "ohio": "USA",
    "massachusetts": "USA", "illinois": "USA", "georgia": "USA",
    # UK
    "london": "UK", "manchester": "UK", "edinburgh": "UK",
    "birmingham": "UK", "glasgow": "UK", "liverpool": "UK",
    "bristol": "UK", "leeds": "UK", "sheffield": "UK",
    "newcastle": "UK", "oxford": "UK", "cambridge": "UK",
    "cardiff": "UK", "belfast": "UK", "nottingham": "UK",
    "leicester": "UK", "coventry": "UK", "bradford": "UK",
    # Australia
    "sydney": "Australia", "melbourne": "Australia", "brisbane": "Australia",
    "perth": "Australia", "adelaide": "Australia", "gold coast": "Australia",
    "canberra": "Australia", "darwin": "Australia", "hobart": "Australia",
    # Canada
    "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada",
    "calgary": "Canada", "edmonton": "Canada", "ottawa": "Canada",
    "winnipeg": "Canada", "quebec": "Canada", "halifax": "Canada",
    # Germany
    "berlin": "Germany", "munich": "Germany", "hamburg": "Germany",
    "cologne": "Germany", "frankfurt": "Germany", "stuttgart": "Germany",
    "dusseldorf": "Germany", "dortmund": "Germany", "essen": "Germany",
    "leipzig": "Germany", "bremen": "Germany", "dresden": "Germany",
    "hannover": "Germany", "nuremberg": "Germany", "münchen": "Germany",
    "köln": "Germany", "düsseldorf": "Germany",
    # France
    "paris": "France", "lyon": "France", "marseille": "France",
    "toulouse": "France", "nice": "France", "nantes": "France",
    "strasbourg": "France", "bordeaux": "France", "lille": "France",
    # Netherlands
    "amsterdam": "Netherlands", "rotterdam": "Netherlands",
    "the hague": "Netherlands", "utrecht": "Netherlands",
    "eindhoven": "Netherlands", "den haag": "Netherlands",
    # Italy
    "rome": "Italy", "milan": "Italy", "naples": "Italy",
    "turin": "Italy", "palermo": "Italy", "genoa": "Italy",
    "bologna": "Italy", "florence": "Italy", "venice": "Italy",
    "verona": "Italy", "como": "Italy", "bergamo": "Italy",
    "brescia": "Italy", "milano": "Italy", "roma": "Italy",
    "firenze": "Italy", "venezia": "Italy",
    # Other
    "zurich": "Other", "geneva": "Other", "bern": "Other",
    "vienna": "Other", "brussels": "Other", "stockholm": "Other",
    "oslo": "Other", "copenhagen": "Other", "helsinki": "Other",
    "madrid": "Other", "barcelona": "Other", "lisbon": "Other",
    "dublin": "Other", "warsaw": "Other", "prague": "Other",
    "budapest": "Other", "athens": "Other", "tokyo": "Other",
    "beijing": "Other", "shanghai": "Other", "hong kong": "Other",
    "singapore": "Other", "dubai": "Other", "johannesburg": "Other",
    "cape town": "Other", "são paulo": "Other", "buenos aires": "Other",
    "mexico city": "Other", "new zealand": "Other", "auckland": "Other",
}

OCCASION_KEYWORDS: dict[str, list[str]] = {
    "honeymoon": ["honeymoon", "honey moon", "just married", "newlywed", "newly wed"],
    "anniversary": ["anniversary", "wedding anniversary", "years together", "years married"],
    "birthday": ["birthday", "birthday present", "birthday gift", "celebrate a birthday",
                 "birthday treat", "birthday trip", "my birthday", "her birthday", "his birthday"],
    "family": ["family", "kids", "children", "our family", "my kids", "my daughter",
               "my son", "grandchildren", "grandkids", "with my mom", "with my dad",
               "family trip", "family vacation", "family holiday"],
    "hen_party": ["hen party", "bachelorette", "hen do", "girls trip", "girl trip",
                  "girls weekend", "hen night", "stagette"],
    "solo": ["solo trip", "by myself", "traveling alone", "travelling alone", "solo traveler",
             "solo traveller", "on my own", "just me"],
    "friends": ["my friends", "group of friends", "friends trip", "with friends",
                "girlfriends", "boyfriend", "girlfriend"],
    "business": ["corporate", "team building", "business trip", "work trip", "colleagues"],
}

# ─────────────────────────────────────────────────────────────────────────────
# Target URLs
# ─────────────────────────────────────────────────────────────────────────────
CESARINE_COMO_URLS = [
    ("Beatrice", "Como", "https://cesarine.com/en/experiences/cooking-class-in-the-center-of-como-Rq1pqCtQs2"),
    ("Vincenzo", "Como", "https://cesarine.com/en/experiences/cooking-class-on-lake-como-cuisine-and-hospitality-H3WJsAsAmn"),
    ("Monica", "Como", "https://cesarine.com/en/experiences/cooking-class-in-como-let-s-prepare-ravioli-with-herbs-RT4GgNuf9Q"),
    ("Francesca", "Como", "https://cesarine.com/en/experiences/enjoy-handmade-pasta-spwDRoW5cl"),
    ("Margherita", "Como", "https://cesarine.com/en/experiences/italian-flavors-risotto-pasta-and-irresistible-tiramisu-WlIBUJcsUn"),
    ("Margherita", "Como", "https://cesarine.com/en/experiences/grandma-does-it-best-easy-and-tasty-family-recipes-q8WwVTrRBX"),
    ("Lidia", "Como", "https://cesarine.com/en/experiences/cooking-class-with-2-pasta-and-tiramisu-recipes-bczNWzJhGt"),
    ("Valentina", "Como", "https://cesarine.com/en/experiences/grandma-jolanda-s-recipes-r8Ud8jIXaR"),
    ("Federico", "Como", "https://cesarine.com/en/experiences/pizzoccheri-and-tiramisu-on-lake-como-l6VfXTH5UH"),
    ("Francesca", "Como", "https://cesarine.com/en/experiences/pasta-lovers-authentic-italian-cooking-class-pnKYSme62n"),
    ("Vincenzo", "Como", "https://cesarine.com/en/experiences/pizza-napoletana-doc-and-baking-in-a-wood-fired-oven-in-como-pn2UyHcuW8"),
    ("Beatrice", "Como", "https://cesarine.com/en/experiences/small-group-hands-on-cooking-class-pasta-and-tiramisu-r7mnYQyvW1"),
    ("Monica", "Varenna", "https://cesarine.com/en/experiences/cooking-class-at-the-home-of-a-cesarina-in-varenna-CNCplrRanG"),
    ("Monica", "Varenna", "https://cesarine.com/en/experiences/small-group-pasta-and-tiramisu-class-in-varenna-KLSXpTgP6s"),
    ("Margherita", "Como", "https://cesarine.com/en/experiences/a-taste-of-home-let-s-prepare-family-recipes-together-CBL6sW3RWM"),
    ("Annamaria", "Varenna", "https://cesarine.com/en/experiences/market-tour-cooking-class-in-varenna-traditions-produce-LRDBoQhudd"),
]

CESARINE_GARDA_URLS = [
    ("Mariolina", "Desenzano", "https://cesarine.com/en/experiences/at-the-table-with-the-flavors-of-the-italian-tradition-Tt1RJIySmm"),
    ("Marina", "Garda", "https://cesarine.com/en/experiences/traditional-cooking-course-the-flavors-of-lake-garda-GxFDuhNdrH"),
]

CESARINE_MAGGIORE_URLS = [
    ("Gabriella", "Stresa", "https://cesarine.com/en/experiences/fresh-pasta-cooking-class-with-a-view-of-lake-maggiore-9BcVg3geNM"),
    ("Gisella", "Stresa", "https://cesarine.com/en/experiences/culinary-experience-at-a-cesarina-s-home-in-stresa-Xc4lIsaScN"),
]

CESARINE_ISEO_URLS = [
    ("Paolina", "Franciacorta", "https://cesarine.com/en/experiences/from-the-lake-to-the-countryside-W1nkrzIUFT"),
]

TRIPADVISOR_COMO_URLS = [
    ("Cesarine", "Como", "https://www.tripadvisor.com/AttractionProductReview-g187835-d14771081-Home_Cooking_Class_Meal_with_a_Local_in_Como-Como_Lake_Como_Lombardy.html"),
    ("Unknown", "Como", "https://www.tripadvisor.com/AttractionProductReview-g187835-d15098025-Traditional_Cooking_Class_with_Views_of_Lake_Como_and_the_Alps-Como_Lake_Como_Lomb.html"),
    ("Unknown", "Como", "https://www.tripadvisor.com/AttractionProductReview-g187835-d33092465-Como_cooking_class_Pasta_and_Tiramisu-Como_Lake_Como_Lombardy.html"),
    ("Unknown", "Bellagio", "https://www.tripadvisor.com/AttractionProductReview-g187834-d27785000-Bellagio_Cooking_Class_in_the_Village_Villa_Melzi-Bellagio_Lake_Como_Lombardy.html"),
    ("Amy", "Como", "https://www.tripadvisor.com/Attraction_Review-g187835-d9738922-Reviews-Amy_s_Cucina-Como_Lake_Como_Lombardy.html"),
    ("Genevieve", "Sala Comacina", "https://www.tripadvisor.com/Attraction_Review-g664198-d25794906-Reviews-Cooking_on_Lake_Como-Sala_Comacina_Lake_Como_Lombardy.html"),
    ("Unknown", "Varenna", "https://www.tripadvisor.com/Attraction_Review-g187837-d24167474-Reviews-Chef_s_Table_Experience_COOKING_CLASS-Varenna_Lake_Como_Lombardy.html"),
    ("Monica", "Varenna", "https://www.tripadvisor.com/Attraction_Review-g187837-d21143094-Reviews-Cesarine_Cooking_Class-Varenna_Lake_Como_Lombardy.html"),
    ("Cesarine", "Como", "https://www.tripadvisor.com/Attraction_Review-g187835-d19531424-Reviews-Cesarine_Como-Como_Lake_Como_Lombardy.html"),
]

TRIPADVISOR_GARDA_URLS = [
    ("Maria", "Manerba del Garda", "https://www.tripadvisor.com/Attraction_Review-g664151-d14049817-Reviews-Good_Food_Good_Mood_Cooking_Class_Garda_Lake-Manerba_del_Garda_Province_of_Bresc.html"),
    ("Andrea", "Torri del Benaco", "https://www.tripadvisor.com/Attraction_Review-g659317-d1138240-Reviews-Le_Gemme_di_Artemisia-Torri_del_Benaco_Province_of_Verona_Veneto.html"),
    ("Unknown", "Lazise", "https://www.tripadvisor.com/AttractionProductReview-g194789-d23939053-Cooking_Class_Fresh_Pasta_Course_with_Wines_at_Lake_Garda-Lazise_Province_of_Veron.html"),
]

TRIPADVISOR_MAGGIORE_URLS = [
    ("Marco Bosco", "Stresa", "https://www.tripadvisor.com/AttractionProductReview-g187847-d14170333-Traditional_Italian_Dishes_Cooking_Class_in_Lake_Maggiore-Stresa_Lake_Maggiore_Pie.html"),
    ("Francesca", "Colazza", "https://www.tripadvisor.com/Attraction_Review-g2050024-d6440207-Reviews-Cook_on_the_Lakes-Colazza_Lake_Maggiore_Piedmont.html"),
    ("Unknown", "Baveno", "https://www.tripadvisor.com/AttractionProductReview-g187844-d15102009-Dine_Enjoy_a_Cooking_Demo_at_Local_s_Home_in_Lake_Maggiore-Baveno_Lake_Maggiore_Pi.html"),
    ("Unknown", "Stresa", "https://www.tripadvisor.com/AttractionProductReview-g187847-d17799507-Private_Pasta_Tiramisu_Class_at_a_Cesarina_s_home_with_tasting_Lake_Maggiore-Stres.html"),
]

TRIPADVISOR_TUSCANY_URLS = [
    ("Walkabout", "Florence", "https://www.tripadvisor.com/Attraction_Review-g187895-d10435299-Reviews-Cooking_Class_in_Florence-Florence_Tuscany.html"),
]

AIRBNB_COMO_URLS = [
    ("Annamaria", "Lierna", "https://www.airbnb.com/experiences/230299"),
    ("Genevieve", "Sala Comacina", "https://www.airbnb.com/experiences/4327218"),
    ("Valentina", "Albavilla", "https://www.airbnb.com/experiences/131810"),
    ("Katie", "Como", "https://www.airbnb.com/experiences/72645"),
]

COMPETITOR_SITES: list[tuple[str, str, str, str]] = [
    # (host, city, region, url)
    ("Debora", "Como", "Como", "https://cookingclasslakecomo.it/en/"),
    ("Marco", "Como", "Como", "https://www.comocookingclass.com/"),
    ("Paola", "Como", "Como", "https://www.passionandcooking.com/culinary-experience-nutrition-lifestyle/"),
    ("Amy", "Como", "Como", "https://amyscucina.com/"),
    ("Unknown", "Como", "Como", "https://lakecomoexperiences.com/experiences/cooking-class-with-lake-view-in-como/"),
    ("Genevieve", "Como", "Como", "https://lakecomokitchen.co/"),
    ("Maria", "Manerba del Garda", "Garda", "https://goodfoodgoodmood.it/en/cooking-class-culinary-school/"),
    ("Canevin", "Garda", "Garda", "https://www.canevincookingclass.com/en/"),
    ("Fabio", "Florence", "Tuscany", "https://www.travelingspoon.com/hosts/7687-authentic-florence-cooking-class-in-the-tuscan-countryside"),
    ("Erika", "Florence", "Tuscany", "https://www.cookingclassesintuscany.net/press-and-reviews/"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def random_sleep(min_s: float = 2.0, max_s: float = 5.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }


def detect_language(text: str) -> str:
    if not LANGDETECT_AVAILABLE or not text.strip():
        return "EN"
    try:
        code = detect(text)
        mapping = {"en": "EN", "it": "IT", "de": "DE", "fr": "FR", "es": "ES", "nl": "NL"}
        return mapping.get(code, "Other")
    except Exception:
        return "EN"


def infer_country(location: str) -> str:
    if not location:
        return "Unknown"
    loc_lower = location.lower().strip()
    for city, country in CITY_TO_COUNTRY.items():
        if city in loc_lower:
            return country
    # State abbreviations → USA
    us_states = {"ny", "ca", "tx", "fl", "il", "pa", "oh", "ga", "nc", "mi",
                 "nj", "va", "wa", "az", "ma", "tn", "in", "mo", "md", "wi",
                 "mn", "co", "al", "sc", "la", "ky", "or", "ok", "ct", "ut",
                 "nv", "ia", "ms", "ar", "ks", "ne", "id", "nm", "wv", "nh",
                 "me", "ri", "de", "sd", "nd", "ak", "vt", "wy", "mt", "hi"}
    parts = re.split(r"[,\s]+", loc_lower)
    if any(p in us_states for p in parts):
        return "USA"
    return "Unknown"


def detect_occasion(text: str) -> str:
    text_lower = text.lower()
    for occasion, keywords in OCCASION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return occasion
    return "unknown"


def is_duplicate(new_review: dict, existing_set: set) -> bool:
    key = (
        new_review.get("reviewer_name", "").lower().strip(),
        new_review.get("review_text", "")[:50].lower().strip(),
    )
    return key in existing_set


def make_key(review: dict) -> tuple:
    return (
        review.get("reviewer_name", "").lower().strip(),
        review.get("review_text", "")[:50].lower().strip(),
    )


def clean_text(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def log_progress(message: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line)
    with open(PROGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Database management
# ─────────────────────────────────────────────────────────────────────────────

class ReviewDatabase:
    def __init__(self):
        self.reviews: list[dict] = []
        self.seen_keys: set = set()
        self.next_id = 1
        self._load_existing()

    def _load_existing(self):
        """Load existing reviews_database.csv if present."""
        if Path(CSV_FILE).exists():
            df = pd.read_csv(CSV_FILE, encoding="utf-8")
            for _, row in df.iterrows():
                review = row.to_dict()
                self.reviews.append(review)
                self.seen_keys.add(make_key(review))
            self.next_id = len(self.reviews) + 1
            log_progress(f"Loaded {len(self.reviews)} existing reviews from {CSV_FILE}")

    def add(self, review: dict) -> bool:
        if is_duplicate(review, self.seen_keys):
            return False
        review["id"] = self.next_id
        self.next_id += 1
        self.reviews.append(review)
        self.seen_keys.add(make_key(review))
        return True

    def save(self):
        df = pd.DataFrame(self.reviews, columns=CSV_COLUMNS)
        df.to_csv(CSV_FILE, index=False, encoding="utf-8")
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reviews, f, ensure_ascii=False, indent=2)
        log_progress(f"Saved {len(self.reviews)} reviews → {CSV_FILE} + {JSON_FILE}")

    def __len__(self):
        return len(self.reviews)


# ─────────────────────────────────────────────────────────────────────────────
# Cesarine scraper (plain HTTP + BeautifulSoup)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_cesarine_page(url: str, host_name: str, city: str, region: str, db: ReviewDatabase) -> int:
    """Scrape a single Cesarine experience page and return new review count."""
    added = 0
    try:
        random_sleep(2, 4)
        resp = requests.get(url, headers=random_headers(), timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try multiple selectors for review blocks
        review_blocks = (
            soup.select("div[class*='review']")
            or soup.select("div[class*='Review']")
            or soup.select("article[class*='review']")
            or soup.select(".review-item")
            or soup.select("[data-testid='review']")
        )

        if not review_blocks:
            # Fallback: look for common Cesarine structure
            review_blocks = soup.find_all("div", class_=re.compile(r"review", re.I))

        for block in review_blocks:
            # Extract reviewer name
            name_el = (
                block.find(class_=re.compile(r"name|author|reviewer", re.I))
                or block.find("strong")
                or block.find("h3")
                or block.find("h4")
            )
            reviewer_name = clean_text(name_el.get_text()) if name_el else "Unknown"

            # Extract date
            date_el = block.find(class_=re.compile(r"date|time", re.I)) or block.find("time")
            date_str = clean_text(date_el.get_text()) if date_el else ""
            date_str = parse_date(date_str)

            # Extract rating
            rating = extract_rating_from_block(block)

            # Extract review text
            text_el = (
                block.find(class_=re.compile(r"text|body|content|comment", re.I))
                or block.find("p")
            )
            review_text = clean_text(text_el.get_text()) if text_el else ""

            if not review_text or len(review_text.split()) < 5:
                continue

            review = build_review(
                platform="Cesarine",
                region=region,
                city=city,
                host_name=host_name,
                reviewer_name=reviewer_name,
                reviewer_location="",
                reviewer_country="Unknown",
                rating=rating,
                date=date_str,
                review_text=review_text,
                url=url,
            )
            if db.add(review):
                added += 1

    except requests.HTTPError as e:
        logger.error(f"HTTP error scraping Cesarine {url}: {e}")
    except Exception as e:
        logger.error(f"Error scraping Cesarine {url}: {e}")

    return added


def scrape_cesarine_playwright(url: str, host_name: str, city: str, region: str, db: ReviewDatabase) -> int:
    """Use Playwright to scrape Cesarine if plain HTTP yielded 0 reviews."""
    if not PLAYWRIGHT_AVAILABLE:
        return 0
    added = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            random_sleep(2, 4)

            # Click "Show more reviews" if present
            for _ in range(10):
                try:
                    btn = page.locator("button:has-text('more'), button:has-text('More'), "
                                       "a:has-text('more reviews'), [class*='load-more']").first
                    if btn.is_visible():
                        btn.click()
                        random_sleep(1.5, 3)
                    else:
                        break
                except Exception:
                    break

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        review_blocks = soup.find_all("div", class_=re.compile(r"review", re.I))

        for block in review_blocks:
            name_el = block.find(class_=re.compile(r"name|author", re.I)) or block.find("strong")
            reviewer_name = clean_text(name_el.get_text()) if name_el else "Unknown"

            date_el = block.find(class_=re.compile(r"date|time", re.I)) or block.find("time")
            date_str = parse_date(clean_text(date_el.get_text()) if date_el else "")

            rating = extract_rating_from_block(block)

            text_el = block.find(class_=re.compile(r"text|body|content|comment", re.I)) or block.find("p")
            review_text = clean_text(text_el.get_text()) if text_el else ""

            if not review_text or len(review_text.split()) < 5:
                continue

            review = build_review(
                platform="Cesarine",
                region=region,
                city=city,
                host_name=host_name,
                reviewer_name=reviewer_name,
                reviewer_location="",
                reviewer_country="Unknown",
                rating=rating,
                date=date_str,
                review_text=review_text,
                url=url,
            )
            if db.add(review):
                added += 1

    except Exception as e:
        logger.error(f"Playwright error scraping Cesarine {url}: {e}")

    return added


# ─────────────────────────────────────────────────────────────────────────────
# TripAdvisor scraper (Playwright required)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_tripadvisor(url: str, host_name: str, city: str, region: str, db: ReviewDatabase,
                       max_pages: int = 30) -> int:
    """Scrape TripAdvisor reviews using Playwright with pagination."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available – skipping TripAdvisor")
        return 0

    added = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            current_url = url
            for page_num in range(max_pages):
                try:
                    page.goto(current_url, wait_until="networkidle", timeout=30000)
                    random_sleep(3, 5)

                    # Expand truncated reviews
                    try:
                        more_btn = page.locator("button:has-text('More'), span:has-text('Read more')").first
                        if more_btn.is_visible():
                            more_btn.click()
                            random_sleep(1, 2)
                    except Exception:
                        pass

                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    # TripAdvisor review blocks
                    blocks = (
                        soup.select("div[data-automation='reviewCard']")
                        or soup.select("div[class*='review-container']")
                        or soup.select("div[class*='reviewSelector']")
                        or soup.select(".reviewSelector")
                        or soup.find_all("div", attrs={"data-reviewid": True})
                    )

                    if not blocks:
                        logger.warning(f"No review blocks found on {current_url} page {page_num}")
                        break

                    page_added = 0
                    for block in blocks:
                        reviewer_name, reviewer_location = extract_ta_reviewer(block)
                        reviewer_country = infer_country(reviewer_location)
                        date_str = extract_ta_date(block)
                        rating = extract_rating_from_block(block)
                        review_text = extract_ta_text(block)

                        if not review_text or len(review_text.split()) < 5:
                            continue

                        review = build_review(
                            platform="TripAdvisor",
                            region=region,
                            city=city,
                            host_name=host_name,
                            reviewer_name=reviewer_name,
                            reviewer_location=reviewer_location,
                            reviewer_country=reviewer_country,
                            rating=rating,
                            date=date_str,
                            review_text=review_text,
                            url=current_url,
                        )
                        if db.add(review):
                            added += 1
                            page_added += 1

                    log_progress(f"TripAdvisor {city} page {page_num}: +{page_added} reviews, total DB: {len(db)}")

                    # Navigate to next page
                    next_url = get_ta_next_page_url(current_url, soup, page_num)
                    if not next_url or page_added == 0:
                        break
                    current_url = next_url
                    random_sleep(3, 6)

                except PWTimeout:
                    logger.error(f"Timeout on TripAdvisor {current_url}")
                    break

            browser.close()

    except Exception as e:
        logger.error(f"Error scraping TripAdvisor {url}: {e}")

    return added


def extract_ta_reviewer(block) -> tuple[str, str]:
    """Extract reviewer name and location from TripAdvisor review block."""
    name = "Unknown"
    location = ""

    name_el = (
        block.find(attrs={"class": re.compile(r"memberOverlayLink|username|info_text", re.I)})
        or block.find(class_=re.compile(r"name", re.I))
    )
    if name_el:
        name = clean_text(name_el.get_text())

    loc_el = block.find(class_=re.compile(r"location|hometown|userLocation", re.I))
    if loc_el:
        location = clean_text(loc_el.get_text())

    return name, location


def extract_ta_date(block) -> str:
    date_el = (
        block.find(class_=re.compile(r"date|ratingDate|writtenDate", re.I))
        or block.find("time")
    )
    if date_el:
        # Try datetime attribute first
        dt = date_el.get("datetime") or date_el.get("title") or date_el.get_text()
        return parse_date(clean_text(str(dt)))
    return ""


def extract_ta_text(block) -> str:
    text_el = (
        block.find(class_=re.compile(r"reviewText|entry|partial_entry|review-content", re.I))
        or block.find(attrs={"data-automation": "reviewText"})
        or block.find("q")
        or block.find("p")
    )
    return clean_text(text_el.get_text()) if text_el else ""


def get_ta_next_page_url(current_url: str, soup, current_page_num: int) -> Optional[str]:
    """Build next TripAdvisor page URL using -orXX- pagination."""
    # Pattern: -or0-, -or10-, -or20-, etc.
    or_pattern = re.compile(r"-or(\d+)-")
    match = or_pattern.search(current_url)

    # Check if "next" button exists in soup
    next_btn = (
        soup.find("a", class_=re.compile(r"next", re.I))
        or soup.find(attrs={"aria-label": re.compile(r"next", re.I)})
    )

    if not next_btn and not match and current_page_num == 0:
        # Try to insert -or10- into the URL for page 2
        pass

    offset = 0
    if match:
        offset = int(match.group(1)) + 10
        return or_pattern.sub(f"-or{offset}-", current_url)
    elif current_page_num == 0 and next_btn:
        # Insert or10 into URL
        parts = current_url.rsplit("-Reviews-", 1)
        if len(parts) == 2:
            return parts[0] + f"-or10-Reviews-" + parts[1]
        parts = current_url.rsplit(".html", 1)
        if len(parts) == 2:
            return parts[0] + "-or10" + ".html"

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Airbnb scraper (Playwright required)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_airbnb(url: str, host_name: str, city: str, db: ReviewDatabase) -> int:
    """Scrape Airbnb Experience reviews using Playwright."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available – skipping Airbnb")
        return 0

    added = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=45000)
            random_sleep(3, 5)

            # Click "Show all reviews"
            for selector in [
                "button:has-text('Show all')",
                "button:has-text('reviews')",
                "a:has-text('reviews')",
                "[data-testid='pdp-show-all-reviews-button']",
            ]:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        random_sleep(2, 4)
                        break
                except Exception:
                    continue

            # Scroll to load all reviews
            for _ in range(20):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                random_sleep(1.5, 3)
                try:
                    more = page.locator("button:has-text('Show more'), button:has-text('Load more')").first
                    if more.is_visible(timeout=2000):
                        more.click()
                        random_sleep(1.5, 3)
                except Exception:
                    pass

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        review_blocks = (
            soup.select("[data-testid='pdp-review-card']")
            or soup.select("[data-testid='review']")
            or soup.find_all("div", class_=re.compile(r"review", re.I))
        )

        for block in review_blocks:
            # Name
            name_el = block.find(class_=re.compile(r"name|author", re.I)) or block.find("h3") or block.find("strong")
            reviewer_name = clean_text(name_el.get_text()) if name_el else "Unknown"

            # Location (Airbnb shows city)
            loc_el = block.find(class_=re.compile(r"location|city|hometown", re.I))
            reviewer_location = clean_text(loc_el.get_text()) if loc_el else ""
            reviewer_country = infer_country(reviewer_location)

            # Date
            date_el = block.find(class_=re.compile(r"date|time", re.I)) or block.find("time")
            date_str = parse_date(clean_text(date_el.get_text()) if date_el else "")

            # Text
            text_el = (
                block.find(class_=re.compile(r"comment|text|body|review-content", re.I))
                or block.find("span", class_=re.compile(r"comment", re.I))
                or block.find("p")
            )
            review_text = clean_text(text_el.get_text()) if text_el else ""

            if not review_text or len(review_text.split()) < 5:
                continue

            review = build_review(
                platform="Airbnb",
                region="Como",
                city=city,
                host_name=host_name,
                reviewer_name=reviewer_name,
                reviewer_location=reviewer_location,
                reviewer_country=reviewer_country,
                rating=5.0,  # Airbnb experiences default to 5-star display
                date=date_str,
                review_text=review_text,
                url=url,
            )
            if db.add(review):
                added += 1

        log_progress(f"Airbnb {host_name} ({city}): +{added} reviews, total DB: {len(db)}")

    except Exception as e:
        logger.error(f"Error scraping Airbnb {url}: {e}")

    return added


# ─────────────────────────────────────────────────────────────────────────────
# Competitor / blog sites scraper (plain HTTP)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_generic_site(url: str, host_name: str, city: str, region: str, db: ReviewDatabase) -> int:
    """Generic scraper for competitor/blog sites using BeautifulSoup."""
    added = 0
    try:
        random_sleep(2, 4)
        resp = requests.get(url, headers=random_headers(), timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for testimonial/review sections
        review_blocks = (
            soup.select(".testimonial, .review, .review-item, .testimonials-item")
            or soup.find_all(class_=re.compile(r"testimonial|review|comment", re.I))
        )

        for block in review_blocks:
            text = clean_text(block.get_text())
            if len(text.split()) < 10:
                continue

            # Try to extract name
            name_el = block.find(class_=re.compile(r"name|author", re.I)) or block.find("cite") or block.find("strong")
            reviewer_name = clean_text(name_el.get_text()) if name_el else "Unknown"

            review = build_review(
                platform="Собственный сайт",
                region=region,
                city=city,
                host_name=host_name,
                reviewer_name=reviewer_name,
                reviewer_location="",
                reviewer_country="Unknown",
                rating=None,
                date="",
                review_text=text,
                url=url,
            )
            if db.add(review):
                added += 1

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")

    return added


# ─────────────────────────────────────────────────────────────────────────────
# Viator scraper (Playwright)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_viator(url: str, host_name: str, city: str, region: str, db: ReviewDatabase) -> int:
    if not PLAYWRIGHT_AVAILABLE:
        return 0

    added = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=45000)
            random_sleep(3, 5)

            # Click "Show more reviews" repeatedly
            for _ in range(50):
                try:
                    btn = page.locator("button:has-text('Show more reviews'), "
                                       "button:has-text('Load more'), "
                                       "[data-test-id='load-more']").first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        random_sleep(2, 4)
                    else:
                        break
                except Exception:
                    break

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        blocks = (
            soup.select("[class*='review-container']")
            or soup.select("[class*='ReviewItem']")
            or soup.find_all("div", class_=re.compile(r"review", re.I))
        )

        for block in blocks:
            name_el = block.find(class_=re.compile(r"name|author|reviewer", re.I))
            reviewer_name = clean_text(name_el.get_text()) if name_el else "Unknown"

            date_el = block.find(class_=re.compile(r"date|time", re.I)) or block.find("time")
            date_str = parse_date(clean_text(date_el.get_text()) if date_el else "")

            rating = extract_rating_from_block(block)

            text_el = (
                block.find(class_=re.compile(r"text|comment|body|content", re.I))
                or block.find("p")
            )
            review_text = clean_text(text_el.get_text()) if text_el else ""

            if not review_text or len(review_text.split()) < 5:
                continue

            review = build_review(
                platform="Viator",
                region=region,
                city=city,
                host_name=host_name,
                reviewer_name=reviewer_name,
                reviewer_location="",
                reviewer_country="Unknown",
                rating=rating,
                date=date_str,
                review_text=review_text,
                url=url,
            )
            if db.add(review):
                added += 1

    except Exception as e:
        logger.error(f"Error scraping Viator {url}: {e}")

    return added


# ─────────────────────────────────────────────────────────────────────────────
# Utility: build review dict
# ─────────────────────────────────────────────────────────────────────────────

def build_review(
    platform: str, region: str, city: str, host_name: str,
    reviewer_name: str, reviewer_location: str, reviewer_country: str,
    rating: Optional[float], date: str, review_text: str, url: str,
) -> dict:
    return {
        "id": None,  # assigned by DB
        "platform": platform,
        "region": region,
        "city": city,
        "host_name": host_name,
        "reviewer_name": reviewer_name,
        "reviewer_location": reviewer_location,
        "reviewer_country": reviewer_country,
        "language": detect_language(review_text),
        "rating": rating,
        "date": date,
        "occasion": detect_occasion(review_text),
        "review_text": review_text,
        "url": url,
    }


def extract_rating_from_block(block) -> Optional[float]:
    """Try to extract star rating from a review block."""
    # Aria-label like "5 of 5 stars" or "Rated 4.5 out of 5"
    rated_el = block.find(attrs={"aria-label": re.compile(r"\d.*star", re.I)})
    if rated_el:
        m = re.search(r"(\d+(?:\.\d+)?)", rated_el.get("aria-label", ""))
        if m:
            return float(m.group(1))

    # SVG filled stars count
    filled = len(block.select("svg[class*='filled'], svg[class*='active'], .ui_bubble_rating"))
    if filled:
        return float(min(filled, 5))

    # Data attributes
    for attr in ["data-rating", "data-score", "data-stars"]:
        el = block.find(attrs={attr: True})
        if el:
            try:
                return float(el[attr])
            except ValueError:
                pass

    # Text search for "X/5" or "X out of 5"
    text = block.get_text()
    m = re.search(r"(\d(?:\.\d)?)\s*/\s*5|(\d(?:\.\d)?)\s*out\s*of\s*5", text, re.I)
    if m:
        return float(m.group(1) or m.group(2))

    return None


def parse_date(raw: str) -> str:
    """Normalize various date strings to YYYY-MM or YYYY-MM-DD."""
    if not raw:
        return ""
    raw = raw.strip()
    # ISO format
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Month Year (e.g. "January 2024", "Jan 2024")
    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "jun": "06", "jul": "07", "aug": "08", "sep": "09",
        "oct": "10", "nov": "11", "dec": "12",
    }
    m = re.search(r"([a-z]+)\s+(\d{4})", raw.lower())
    if m and m.group(1) in months:
        return f"{m.group(2)}-{months[m.group(1)]}"
    # DD/MM/YYYY or MM/DD/YYYY
    m = re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # Just year
    m = re.search(r"\b(\d{4})\b", raw)
    if m:
        return m.group(1)
    return raw[:10]


# ─────────────────────────────────────────────────────────────────────────────
# Load existing reviews from markdown files
# ─────────────────────────────────────────────────────────────────────────────

def load_reviews_from_markdown(filepath: str, db: ReviewDatabase) -> int:
    """
    Parse manually collected reviews from markdown files.
    Expected format: reviewer name, rating, date, text blocks.
    """
    if not Path(filepath).exists():
        logger.warning(f"Markdown file not found: {filepath}")
        return 0

    added = 0
    text = Path(filepath).read_text(encoding="utf-8")

    # Try to match common markdown review patterns:
    # **Name** from Location — date
    # ★★★★★
    # "Review text..."
    pattern = re.compile(
        r"\*\*([^*]+)\*\*\s*(?:from\s+([^\n—–-]+?))?[\s—–-]+([^\n]+)?\n"
        r"(?:[★\*]{1,5}[^\n]*\n)?"
        r'["\u201c\u201d]?\s*([^"\u201c\u201d\n]{20,}(?:\n(?!\*\*)[^\n]{0,200})*)["\u201c\u201d]?',
        re.MULTILINE,
    )

    for m in pattern.finditer(text):
        reviewer_name = m.group(1).strip()
        reviewer_location = (m.group(2) or "").strip()
        date_str = parse_date((m.group(3) or "").strip())
        review_text = clean_text(m.group(4))

        if len(review_text.split()) < 10:
            continue

        review = build_review(
            platform="Блог",
            region="Como",
            city="Como",
            host_name="Unknown",
            reviewer_name=reviewer_name,
            reviewer_location=reviewer_location,
            reviewer_country=infer_country(reviewer_location),
            rating=None,
            date=date_str,
            review_text=review_text,
            url=filepath,
        )
        if db.add(review):
            added += 1

    log_progress(f"Loaded {added} reviews from {filepath}")
    return added


# ─────────────────────────────────────────────────────────────────────────────
# Main orchestration
# ─────────────────────────────────────────────────────────────────────────────

def run_all(db: ReviewDatabase) -> None:
    total_added = 0
    save_counter = 0

    def maybe_save(new_count: int) -> None:
        nonlocal save_counter
        save_counter += new_count
        if save_counter >= SAVE_EVERY:
            db.save()
            save_counter = 0

    # ── 0. Load existing markdown files ──────────────────────────────────────
    log_progress("=== Loading existing markdown reviews ===")
    for md_file in [
        "lake-como-FINAL-review-database.md",
        "lake-como-reviews-analysis.md",
        "lake-como-reviews-round2.md",
    ]:
        n = load_reviews_from_markdown(md_file, db)
        total_added += n
        maybe_save(n)

    # ── 1. Cesarine — Como ───────────────────────────────────────────────────
    log_progress("=== Scraping Cesarine Como ===")
    for host, city, url in CESARINE_COMO_URLS:
        log_progress(f"Cesarine: {host} ({city}) — {url}")
        n = scrape_cesarine_page(url, host, city, "Como", db)
        if n == 0 and PLAYWRIGHT_AVAILABLE:
            log_progress(f"  Falling back to Playwright for {url}")
            n = scrape_cesarine_playwright(url, host, city, "Como", db)
        log_progress(f"  → +{n} reviews, total DB: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 2. Cesarine — Garda ──────────────────────────────────────────────────
    log_progress("=== Scraping Cesarine Garda ===")
    for host, city, url in CESARINE_GARDA_URLS:
        n = scrape_cesarine_page(url, host, city, "Garda", db)
        if n == 0 and PLAYWRIGHT_AVAILABLE:
            n = scrape_cesarine_playwright(url, host, city, "Garda", db)
        log_progress(f"  Cesarine Garda {host}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 3. Cesarine — Maggiore ───────────────────────────────────────────────
    log_progress("=== Scraping Cesarine Maggiore ===")
    for host, city, url in CESARINE_MAGGIORE_URLS:
        n = scrape_cesarine_page(url, host, city, "Maggiore", db)
        if n == 0 and PLAYWRIGHT_AVAILABLE:
            n = scrape_cesarine_playwright(url, host, city, "Maggiore", db)
        log_progress(f"  Cesarine Maggiore {host}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 4. Cesarine — Iseo ───────────────────────────────────────────────────
    log_progress("=== Scraping Cesarine Iseo ===")
    for host, city, url in CESARINE_ISEO_URLS:
        n = scrape_cesarine_page(url, host, city, "Iseo", db)
        if n == 0 and PLAYWRIGHT_AVAILABLE:
            n = scrape_cesarine_playwright(url, host, city, "Iseo", db)
        log_progress(f"  Cesarine Iseo {host}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 5. TripAdvisor — Como ────────────────────────────────────────────────
    log_progress("=== Scraping TripAdvisor Como ===")
    for host, city, url in TRIPADVISOR_COMO_URLS:
        log_progress(f"TripAdvisor: {host} ({city})")
        n = scrape_tripadvisor(url, host, city, "Como", db, max_pages=20)
        log_progress(f"  → +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 6. TripAdvisor — Garda ───────────────────────────────────────────────
    log_progress("=== Scraping TripAdvisor Garda ===")
    for host, city, url in TRIPADVISOR_GARDA_URLS:
        n = scrape_tripadvisor(url, host, city, "Garda", db, max_pages=50)
        log_progress(f"  TripAdvisor Garda {host}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 7. TripAdvisor — Maggiore ────────────────────────────────────────────
    log_progress("=== Scraping TripAdvisor Maggiore ===")
    for host, city, url in TRIPADVISOR_MAGGIORE_URLS:
        n = scrape_tripadvisor(url, host, city, "Maggiore", db, max_pages=15)
        log_progress(f"  TripAdvisor Maggiore {host}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 8. TripAdvisor — Tuscany ─────────────────────────────────────────────
    log_progress("=== Scraping TripAdvisor Tuscany ===")
    for host, city, url in TRIPADVISOR_TUSCANY_URLS:
        # Limit to 50 pages (~500 reviews) as requested
        n = scrape_tripadvisor(url, host, city, "Tuscany", db, max_pages=50)
        log_progress(f"  TripAdvisor Tuscany {host}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 9. Airbnb — Como ─────────────────────────────────────────────────────
    log_progress("=== Scraping Airbnb Como ===")
    for host, city, url in AIRBNB_COMO_URLS:
        log_progress(f"Airbnb: {host} ({city})")
        n = scrape_airbnb(url, host, city, db)
        log_progress(f"  → +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── 10. Viator — Tuscany ────────────────────────────────────────────────
    log_progress("=== Scraping Viator Tuscany ===")
    viator_url = "https://www.viator.com/tours/Florence/Cooking-Class-and-Lunch-at-a-Tuscan-Farmhouse-with-Local-Market-Tour-from-Florence/d519-5070FARMHOUSE"
    n = scrape_viator(viator_url, "Walkabout", "Florence", "Tuscany", db)
    log_progress(f"  Viator Tuscany: +{n}, total: {len(db)}")
    total_added += n
    maybe_save(n)

    # ── 11. Competitor / own sites ───────────────────────────────────────────
    log_progress("=== Scraping competitor sites ===")
    for host, city, region, url in COMPETITOR_SITES:
        n = scrape_generic_site(url, host, city, region, db)
        log_progress(f"  {url}: +{n}, total: {len(db)}")
        total_added += n
        maybe_save(n)

    # ── Final save ────────────────────────────────────────────────────────────
    db.save()
    log_progress(f"\n=== DONE === Total new reviews this run: {total_added}, DB size: {len(db)}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Cooking Reviews Scraper — Northern Italian Lakes")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not PLAYWRIGHT_AVAILABLE:
        print("\n⚠  WARNING: Playwright is not installed.")
        print("   Airbnb, TripAdvisor, Viator sources will be SKIPPED.")
        print("   Install with: pip install playwright && playwright install chromium\n")

    db = ReviewDatabase()
    run_all(db)

    print("\nAll done!")
    print(f"CSV: {CSV_FILE} ({len(db)} reviews)")
    print(f"JSON: {JSON_FILE}")
    print(f"Progress log: {PROGRESS_LOG}")
    print(f"Error log: scraping_errors.log")
