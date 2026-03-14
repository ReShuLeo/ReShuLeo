#!/usr/bin/env python3
"""
Analytics script for the cooking reviews database.
Generates statistics and top marketing phrases.
Run after scrape_reviews.py has collected data.
"""

import json
import sys
from pathlib import Path

import pandas as pd

CSV_FILE = "reviews_database.csv"

# sklearn is optional
try:
    from sklearn.feature_extraction.text import CountVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠  scikit-learn not installed — n-gram analysis will be skipped.")
    print("   Install with: pip install scikit-learn\n")


def load_db() -> pd.DataFrame:
    if not Path(CSV_FILE).exists():
        print(f"❌  {CSV_FILE} not found. Run scrape_reviews.py first.")
        sys.exit(1)
    df = pd.read_csv(CSV_FILE, encoding="utf-8")
    print(f"Loaded {len(df)} reviews from {CSV_FILE}\n")
    return df


def print_stats(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("REVIEW DATABASE STATISTICS")
    print("=" * 60)

    print(f"\n📊 Total reviews: {len(df)}")
    print(f"   With text ≥ 20 words: {(df['review_text'].str.split().str.len() >= 20).sum()}")

    print(f"\n🗺  By region:")
    print(df["region"].value_counts().to_string())

    print(f"\n🏙  By city (top 20):")
    print(df["city"].value_counts().head(20).to_string())

    print(f"\n👤 By host (top 20):")
    print(df["host_name"].value_counts().head(20).to_string())

    print(f"\n🌍 By reviewer country:")
    print(df["reviewer_country"].value_counts().to_string())

    print(f"\n🗣  By language:")
    print(df["language"].value_counts().to_string())

    print(f"\n🎉 By occasion:")
    print(df["occasion"].value_counts().to_string())

    print(f"\n📱 By platform:")
    print(df["platform"].value_counts().to_string())

    # Rating stats (only where rating is present)
    rated = df[df["rating"].notna()]
    if len(rated):
        print(f"\n⭐ Rating stats (n={len(rated)}):")
        print(f"   Mean:   {rated['rating'].mean():.2f}")
        print(f"   Median: {rated['rating'].median():.2f}")
        print(f"   5-star: {(rated['rating'] == 5.0).sum()} ({(rated['rating'] == 5.0).mean()*100:.1f}%)")
        print(f"   4-star: {(rated['rating'] == 4.0).sum()} ({(rated['rating'] == 4.0).mean()*100:.1f}%)")

    # Date range
    dated = df[df["date"].notna() & (df["date"] != "")]
    if len(dated):
        print(f"\n📅 Date range: {dated['date'].min()} — {dated['date'].max()}")

    print()


def top_ngrams(df: pd.DataFrame, n: int = 50) -> None:
    if not SKLEARN_AVAILABLE:
        return

    print("=" * 60)
    print(f"TOP {n} MARKETING PHRASES (2-4 word n-grams, English reviews)")
    print("=" * 60)

    en_reviews = df[df["language"] == "EN"]["review_text"].dropna()
    if len(en_reviews) == 0:
        print("No English reviews found for n-gram analysis.")
        return

    vectorizer = CountVectorizer(
        ngram_range=(2, 4),
        stop_words="english",
        max_features=n,
        min_df=2,
    )
    try:
        X = vectorizer.fit_transform(en_reviews)
        phrases = vectorizer.get_feature_names_out()
        counts = X.sum(axis=0).A1
        top = sorted(zip(phrases, counts), key=lambda x: x[1], reverse=True)
        print(f"\n{'Phrase':<50} {'Count':>6}")
        print("-" * 58)
        for phrase, count in top:
            print(f"{phrase:<50} {int(count):>6}")
    except Exception as e:
        print(f"n-gram analysis failed: {e}")

    print()


def export_report(df: pd.DataFrame) -> None:
    """Save a summary JSON report."""
    report = {
        "total_reviews": len(df),
        "reviews_20_words_plus": int((df["review_text"].str.split().str.len() >= 20).sum()),
        "by_region": df["region"].value_counts().to_dict(),
        "by_platform": df["platform"].value_counts().to_dict(),
        "by_country": df["reviewer_country"].value_counts().to_dict(),
        "by_language": df["language"].value_counts().to_dict(),
        "by_occasion": df["occasion"].value_counts().to_dict(),
        "top_hosts": df["host_name"].value_counts().head(20).to_dict(),
        "top_cities": df["city"].value_counts().head(20).to_dict(),
    }
    rated = df[df["rating"].notna()]
    if len(rated):
        report["rating_mean"] = round(float(rated["rating"].mean()), 2)
        report["rating_count"] = len(rated)
        report["five_star_pct"] = round(float((rated["rating"] == 5.0).mean() * 100), 1)

    with open("reviews_analytics_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("Analytics report saved → reviews_analytics_report.json")


if __name__ == "__main__":
    df = load_db()
    print_stats(df)
    top_ngrams(df, n=50)
    export_report(df)
