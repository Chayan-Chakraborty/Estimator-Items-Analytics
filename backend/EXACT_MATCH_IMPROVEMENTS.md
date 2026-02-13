# Exact Match Improvements - Multiple Item Support

## Summary

Enhanced the fuzzy search **Step 1 (Exact Match)** to return **ALL matching items** instead of just one, particularly useful for queries like "table" which matches multiple items.

---

## Problem

**Before:** Query "table" in Step 1 would return only 1 item (the first match found)

**After:** Query "table" in Step 1 returns ALL 7 items containing "table":
- console table
- centre table  
- study table
- bed side table
- side table
- side table kids
- seating - table & chair

---

## Changes Made

### 1. New Function: `extract_all_items()` 

**Location:** `backend/utils/extractor.py`

```python
def extract_all_items(query: str, synonym_index: dict):
    """
    Extract ALL matching item names from a query.
    
    Logic:
    - Single-word queries (e.g., "table") → Returns all items containing that word
    - Multi-word queries (e.g., "study table") → Returns only exact phrase matches
    """
```

**Behavior:**

| Query | Behavior | Results |
|-------|----------|---------|
| `"table"` | Single word → match all | 7 items (console table, centre table, study table, ...) |
| `"study table"` | Multi-word → exact match only | 1 item (study table) |
| `"bed"` | Single word → match all | 8 items (bed, bed bench, bed room, ...) |
| `"bichhana"` | Exact synonym → match | 1 item (bed) |

### 2. Updated Fuzzy Search Step 1

**Location:** `backend/services/itemService.py`

**Before:**
```python
phrase_item = extract_item(query, index)
if phrase_item:
    return [phrase_item]  # Returns only 1 item
```

**After:**
```python
matched_items = extract_all_items(query, index)
if matched_items:
    return matched_items  # Returns ALL matching items
```

---

## Examples

### Example 1: Query "table"

**Step 1 (Exact Match):**
```json
{
  "data": [
    {"itemName": "bed side table", "identifiers": ["BST_ITM_NW"]},
    {"itemName": "centre table", "identifiers": ["CEN_ITM_NW"]},
    {"itemName": "console table", "identifiers": ["COT_ITM_NW"]},
    {"itemName": "side table", "identifiers": ["SIT_ITM_NW"]},
    {"itemName": "side table kids", "identifiers": []},
    {"itemName": "study table", "identifiers": ["STT_ITM_NW"]},
    {"itemName": "seating - table & chair", "identifiers": ["STC_ITM_NW"]}
  ]
}
```

### Example 2: Query "study table"

**Step 1 (Exact Match):**
```json
{
  "data": [
    {"itemName": "study table", "identifiers": ["STT_ITM_NW"]}
  ]
}
```

Only returns the exact phrase match, not other tables.

### Example 3: Query "bed"

**Step 1 (Exact Match):**
```json
{
  "data": [
    {"itemName": "bed", "identifiers": ["BED_ITM_NW"]},
    {"itemName": "bed bench", "identifiers": ["BEB_ITM_NW"]},
    {"itemName": "bed ka kushans", "identifiers": []},
    {"itemName": "bed room", "identifiers": ["BED_ITM_NW"]},
    {"itemName": "bed side table", "identifiers": ["BST_ITM_NW"]},
    {"itemName": "bed, cot", "identifiers": ["BED_ITM_NW"]},
    {"itemName": "mastr bed room cubor", "identifiers": ["MBC_ITM_NW"]},
    {"itemName": "wooden single", "identifiers": []}
  ]
}
```

---

## Combined with Fuzzy Matching

The complete search flow now works as:

1. **Step 1: Exact Match** (NEW - returns multiple items)
   - Single-word: Returns ALL items containing that word
   - Multi-word: Returns only exact phrase matches
   
2. **Step 2: Fuzzy Phrase Match** (IMPROVED with RapidFuzz + length filter)
   - Only runs if Step 1 finds no matches
   - Filters false positives using length-based thresholds
   
3. **Step 3: Token-Level Matching**
   - Only runs if Steps 1 & 2 find no matches
   - Most lenient matching

---

## Testing

### Test in Docker Container:

```bash
# Rebuild container
docker compose down
docker compose up --build backend

# Test single-word query (should return multiple items)
curl "http://localhost:8090/search-items?query=table"

# Test multi-word query (should return 1 item)
curl "http://localhost:8090/search-items?query=study%20table"

# Test with exact synonym
curl "http://localhost:8090/search-items?query=bichhana"
```

### Expected Results:

| Endpoint | Query | Expected Items |
|----------|-------|----------------|
| `/search-items` | `table` | 7 items (all containing "table") |
| `/search-items` | `study table` | 1 item (study table) |
| `/search-items` | `bed` | 8 items (all containing "bed") |
| `/search-items` | `bichhana` | 1 item (bed - exact synonym match) |
| `/search-items` | `bichana` | 2 items (bed + bed bench - fuzzy match with false positives filtered) |

---

## Implementation Details

### How `extract_all_items()` Works:

1. **Normalize Query:** Convert to lowercase, remove repeated characters
2. **Try Phrase Matching:**
   - Check if full query matches a multi-word item
   - If yes, return only that item
3. **Token Matching (for single-word queries):**
   - Look for the word in all synonym index keys
   - Collect ALL items where the token appears
   - Handle both direct matches and word-in-phrase matches

### Key Logic:

```python
# For "table" query:
for token in ["table"]:
    # Direct lookup
    if "table" in synonym_index:
        matched_items.add(synonym_index["table"])
    
    # Check multi-word keys
    for key in ["console table", "study table", "centre table", ...]:
        if "table" in key.split():  # Token appears in key
            matched_items.add(item)  # Add to results
```

---

## Files Modified

1. **`backend/utils/extractor.py`**
   - Added `extract_all_items()` function
   - Added documentation to `extract_item()`

2. **`backend/services/itemService.py`**
   - Imported `extract_all_items`
   - Updated Step 1 to use `extract_all_items()` instead of `extract_item()`

---

## Benefits

✅ **Better User Experience:** "table" query now shows all table types  
✅ **More Accurate:** Multi-word queries still return exact matches only  
✅ **Consistent Behavior:** Matches what users expect from a search system  
✅ **Backwards Compatible:** Doesn't break existing functionality  

---

## Performance

- No significant performance impact
- Synonym index is already built and cached
- Additional items are just collected in a set, no expensive operations

---

## Future Enhancements

1. **Relevance Scoring:** Rank items by relevance (exact name match > token match)
2. **Partial Word Matching:** Support "tab" matching "table"
3. **Category Filtering:** Option to filter by item category
4. **Search History:** Learn from user selections to improve results
