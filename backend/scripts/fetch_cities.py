#!/usr/bin/env python3
"""
Fetch unique cities from the database and generate:
1. city.csv - List of unique city names
2. city_canonical_mapping.json - Mapping of normalized city names to canonical forms

This script connects to the database using credentials from utils.constants.dbCred
and fetches cities from finalized estimators.
"""

import csv
import json
import os
import sys
import unicodedata
import re
from mysql.connector import Error

# -------------------------------------------------
# Ensure project root is on sys.path BEFORE local imports
# -------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# -------------------------------------------------
# Imports from project
# -------------------------------------------------
from dbConfig.mysqlConnectionConfig import get_mysql_connection
from utils.constants import (
    APP_ENVIRONMENT,
    CITY_CSV_PATH,
    CITY_CANONICAL_MAPPING_PATH
)

# -------------------------------------------------
# SQL Query to fetch cities
# -------------------------------------------------

QUERY_CITIES = """
SELECT DISTINCT(a.city) as city
FROM vishanti.estimator e
LEFT JOIN zeus.address a ON a.project_id = e.project_id
WHERE e.status = 'FINALIZED'
  AND a.city IS NOT NULL
  AND TRIM(a.city) != ''
ORDER BY a.city;
"""

# -------------------------------------------------
# Normalization function (similar to extractor.normalize)
# -------------------------------------------------


def normalize_city(text: str) -> str:
    """
    Normalize city name for matching:
    - NFKC Unicode normalization
    - Lowercase
    - Remove special chars (keep alphanumeric and spaces)
    - Collapse multiple spaces
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.lower()

    # Remove zero-width chars
    text = text.replace("\u200c", "").replace("\u200d", "")

    # Keep alphanumeric and spaces, replace others with space
    text = "".join(
        ch if ch.isalnum() or ch.isspace() else " "
        for ch in text
    )

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------------------------------
# Core methods
# -------------------------------------------------


def fetch_cities_from_db(environment: str):
    """
    Fetch unique city names from the database.

    Args:
        environment: Environment name (local, dev, uat, prod)

    Returns:
        list[str]: List of unique city names (non-empty)

    Raises:
        Various exceptions if database connection fails
    """
    connection = None
    cursor = None
    tunnel = None

    try:
        print(f"🔌 Connecting to database (environment: {environment})...")
        connection, tunnel = get_mysql_connection(environment)
        cursor = connection.cursor(dictionary=True)

        print(f"📊 Executing query to fetch cities...")
        cursor.execute(QUERY_CITIES)
        rows = cursor.fetchall()

        if not rows:
            print("⚠️  No cities found in database.")
            return []

        # Extract city names and filter out empty strings
        cities = [
            row['city'].strip()
            for row in rows
            if row.get('city') and row['city'].strip()
        ]

        print(f"✅ Found {len(cities)} unique cities")
        return cities

    except (Error, ValueError) as e:
        print(f"❌ Database error: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        if tunnel:
            tunnel.stop()


def write_cities_csv(cities: list[str], output_file: str):
    """
    Write cities to CSV file.

    Args:
        cities: List of city names
        output_file: Path to output CSV file
    """
    if not cities:
        print("⚠️  No cities to write to CSV")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write CSV with header
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["city"])  # Header
        for city in cities:
            writer.writerow([city])

    print(f"✅ Cities written to {output_file}")


def generate_canonical_mapping(cities: list[str], output_file: str):
    """
    Generate a canonical mapping JSON file for city name normalization.

    Creates a mapping from normalized city names to canonical (original) city names.
    This helps with fuzzy matching and typo tolerance.

    Structure:
    {
        "normalized_city_name": "Canonical City Name",
        "bengaluru": "Bengaluru",
        "bangalore": "Bengaluru",  # if both exist, we keep first
        ...
    }

    Args:
        cities: List of city names
        output_file: Path to output JSON file
    """
    if not cities:
        print("⚠️  No cities to generate mapping")
        return

    mapping = {}
    duplicates = {}

    for city in cities:
        normalized = normalize_city(city)

        if not normalized:
            continue

        if normalized in mapping:
            # Track duplicates for logging
            if normalized not in duplicates:
                duplicates[normalized] = [mapping[normalized]]
            duplicates[normalized].append(city)
        else:
            # First occurrence wins as canonical
            mapping[normalized] = city

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write JSON (sorted for readability)
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(mapping, file, indent=2, ensure_ascii=False, sort_keys=True)

    print(f"✅ Canonical mapping written to {output_file}")
    print(f"   Total mappings: {len(mapping)}")

    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} normalized names with multiple variants:")
        for norm, variants in list(duplicates.items())[:5]:  # Show first 5
            print(f"      '{norm}' -> {variants}")
        if len(duplicates) > 5:
            print(f"      ... and {len(duplicates) - 5} more")


def fetch_and_generate_city_files(environment: str):
    """
    Main workflow:
    1. Fetch cities from database
    2. Write to city.csv
    3. Generate city_canonical_mapping.json

    Args:
        environment: Environment name (local, dev, uat, prod)
    """
    try:
        print("\n" + "="*60)
        print("🌍 City Data Fetch & Generation Script")
        print("="*60)

        # Step 1: Fetch cities from database
        cities = fetch_cities_from_db(environment)

        if not cities:
            print("\n⚠️  No cities found. Skipping file generation.")
            return

        # Step 2: Write CSV
        print(f"\n📝 Writing cities to CSV...")
        write_cities_csv(cities, CITY_CSV_PATH)

        # Step 3: Generate canonical mapping
        print(f"\n🗺️  Generating canonical mapping...")
        generate_canonical_mapping(cities, CITY_CANONICAL_MAPPING_PATH)

        print("\n" + "="*60)
        print("✅ City data fetch and generation completed successfully!")
        print("="*60)
        print(f"   CSV: {CITY_CSV_PATH}")
        print(f"   JSON: {CITY_CANONICAL_MAPPING_PATH}")
        print(f"   Total cities: {len(cities)}")
        print()

    except (Error, ValueError) as e:
        # Don't crash container startup if DB isn't reachable
        print(f"\n⚠️  Skipping city data fetch (cannot connect): {e}")
        print("   Container will continue with existing city files if available.\n")
        return

    except Exception as e:
        # Catch-all for unexpected issues
        print(f"\n⚠️  Unexpected error during city data fetch: {e}")
        print("   Container will continue with existing city files if available.\n")
        import traceback
        traceback.print_exc()
        return


# -------------------------------------------------
# Script entry point
# -------------------------------------------------


if __name__ == "__main__":
    fetch_and_generate_city_files(APP_ENVIRONMENT)
