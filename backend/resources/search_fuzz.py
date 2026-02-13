import json
from rapidfuzz import fuzz, process
from utils.constants import ITEMS_JSON_OUT
# -----------------------------
# Load JSON from file
# -----------------------------
def load_items(file_path=ITEMS_JSON_OUT):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Build Search Index
# -----------------------------
def build_search_index(data):
    search_index = {}

    for main_key, details in data.items():
        # Add main English category
        search_index[main_key.lower()] = main_key

        for lang, values in details.items():
            if lang == "identifiers":
                continue

            # Native words
            for word in values.get("native", "").split(","):
                word = word.strip().lower()
                if word:
                    search_index[word] = main_key

            # Roman words
            for word in values.get("roman", "").split(","):
                word = word.strip().lower()
                if word:
                    search_index[word] = main_key

    return search_index


# -----------------------------
# Multi Match Search
# -----------------------------
def get_multiple_matches(query, search_index, threshold=60, limit=5):
    query = query.lower()

    matches = process.extract(
        query,
        search_index.keys(),
        scorer=fuzz.WRatio,
        limit=limit
    )

    results = []
    seen_categories = set()

    for matched_word, score, _ in matches:
        category = search_index[matched_word]

        if score >= threshold and category not in seen_categories:
            results.append({
                "matched_word": matched_word,
                "category": category,
                "confidence_score": score
            })
            seen_categories.add(category)

    return results


# -----------------------------
# Main Execution
# -----------------------------
def search_fuzz(query):
    data = load_items(ITEMS_JSON_OUT)
    search_index = build_search_index(data)
    return get_multiple_matches(query, search_index)

