# Cooking Reviews Scraper — Northern Italian Lakes

Collects real reviews for cooking classes near Lake Como, Lake Garda, Lake Maggiore, Lake Iseo, and Tuscany. Target: 2,000+ unique reviews for marketing analysis.

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
python scrape_reviews.py        # collect reviews
python analyze_reviews.py       # run analytics
```

## Output Files

| File | Description |
|------|-------------|
| `reviews_database.csv` | All reviews (UTF-8, 14 columns) |
| `reviews_database.json` | Same data in JSON format |
| `reviews_analytics_report.json` | Summary statistics |
| `scraping_progress.log` | Step-by-step progress |
| `scraping_errors.log` | Errors and warnings |

## CSV Columns

`id, platform, region, city, host_name, reviewer_name, reviewer_location, reviewer_country, language, rating, date, occasion, review_text, url`

## Sources (by priority)

1. **Lake Como** — Airbnb Experiences, TripAdvisor, Cesarine (16 listings), competitor sites
2. **Lake Garda** — TripAdvisor, Cesarine
3. **Lake Maggiore** — TripAdvisor, Cesarine
4. **Lake Iseo** — Cesarine
5. **Tuscany/Florence** — TripAdvisor, Viator

## Deduplication

Reviews are deduplicated by `(reviewer_name.lower(), review_text[:50].lower())`. Existing markdown files (`lake-como-FINAL-review-database.md`, etc.) are loaded first so their ~354 reviews are not repeated.

## Requirements

- Python 3.10+
- Playwright + Chromium (for Airbnb, TripAdvisor, Viator)
- BeautifulSoup4 (for Cesarine, own sites)
- langdetect (language detection)
- scikit-learn (n-gram phrase analysis, optional)
