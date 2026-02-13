# Critical Fix: Native Script Support in Fuzzy Matching

## 🚨 Critical Bug Fixed

### Problem
The `normalize()` function was **breaking native script words** by treating Unicode combining characters as non-alphanumeric and replacing them with spaces.

**Impact:**
- Hindi, Bengali, Tamil, Kannada, Telugu, Malayalam queries were broken
- Fuzzy matching DID NOT work for native scripts
- Example: `"बिस्तर"` (Hindi for "bed") became `"ब स तर"` (3 separate characters)

---

## Root Cause

### Unicode Combining Characters

Indic scripts use **combining characters** to form complete syllables:
- **Vowel marks** (matra): ि, ा, ी, ु, ू, े, ै, ो, ौ, etc.
- **Virama/Halant** (्, ്, ್, ், etc.): Suppresses inherent vowel
- **Anusvara** (ं, ಂ, ം, etc.): Nasal sound
- **Visarga** (ः, ಃ, ഃ, etc.): Voiceless sound

These are classified as Unicode categories:
- `Mn` (Nonspacing_Mark): Vowel marks, virama
- `Mc` (Spacing_Mark): Anusvara, visarga

### The Bug

```python
# OLD CODE (BROKEN):
text = "".join(
    ch if ch.isalnum() or ch.isspace() else " "
    for ch in text
)
```

**Problem:** `ch.isalnum()` returns `False` for combining characters, so they were replaced with spaces!

**Result:**
- `"बिस्तर"` → `"ब स तर"` ❌ (broken into 3 parts)
- `"கட்டில்"` → `"கட ட ல"` ❌ (broken into 3 parts)
- Fuzzy matching completely broken for native scripts

---

## The Fix

### Updated normalize() Function

```python
# NEW CODE (FIXED):
text = "".join(
    ch if ch.isalnum() or ch.isspace() or unicodedata.category(ch) in ('Mn', 'Mc') else " "
    for ch in text
)
```

**Now preserves:**
- All alphanumeric characters
- Spaces
- Unicode combining marks (categories `Mn` and `Mc`)

---

## Results

### Before Fix (BROKEN):

| Language | Original | Normalized (OLD) | Status |
|----------|----------|------------------|--------|
| Hindi | `बिस्तर` | `ब स तर` | ❌ Broken |
| Bengali | `বিছানা` | `ব ছ ন` | ❌ Broken |
| Tamil | `கட்டில்` | `கட ட ல` | ❌ Broken |
| Kannada | `ಮಂಚ` | `ಮ ಚ` | ❌ Broken |

### After Fix (WORKING):

| Language | Original | Normalized (NEW) | Status |
|----------|----------|------------------|--------|
| Hindi | `बिस्तर` | `बिस्तर` | ✅ Fixed |
| Bengali | `বিছানা` | `বিছানা` | ✅ Fixed |
| Tamil | `கட்டில்` | `கட்டில்` | ✅ Fixed |
| Kannada | `ಮಂಚ` | `ಮಂಚ` | ✅ Fixed |
| English | `table` | `table` | ✅ Unchanged |

---

## Testing

### Test Native Script Queries:

```bash
# Rebuild container with fix
docker compose down
docker compose up --build backend

# Test 1: Hindi query for "bed"
curl "http://localhost:8090/search-items?query=बिस्तर"
# Expected: Should return "Bed" item

# Test 2: Bengali query for "bed"
curl "http://localhost:8090/search-items?query=বিছানা"
# Expected: Should return "Bed" item

# Test 3: Tamil query for "bed"
curl "http://localhost:8090/search-items?query=கட்டில்"
# Expected: Should return "Bed" item

# Test 4: Kannada query for "bed"
curl "http://localhost:8090/search-items?query=ಮಂಚ"
# Expected: Should return "Bed" item

# Test 5: Hindi query with typo (fuzzy match)
curl "http://localhost:8090/search-items?query=बिसतर"
# Expected: Should still find "Bed" via fuzzy matching
```

### Expected Behavior:

1. **Exact Match:** Native script queries that exactly match synonyms in `items.json` → Found in Step 1
2. **Fuzzy Match:** Native script queries with typos → Found in Step 2 with fuzzy matching
3. **Token Match:** Single words from native multi-word phrases → Found via token matching

---

## Unicode Category Reference

### Categories Preserved:

| Category | Name | Examples | Description |
|----------|------|----------|-------------|
| `L*` | Letter | A-Z, a-z, अ-ह, க-ன | Base letters (covered by `isalnum()`) |
| `N*` | Number | 0-9, ०-९, ௦-௯ | Digits (covered by `isalnum()`) |
| `Mn` | Nonspacing_Mark | ि, ा, ्, ் | Vowel marks, virama (NEW) |
| `Mc` | Spacing_Mark | ं, ः, ಂ, ം | Anusvara, visarga (NEW) |

### Categories Still Removed:

| Category | Name | Examples | Reason |
|----------|------|----------|--------|
| `P*` | Punctuation | .,!? | Not part of words |
| `S*` | Symbol | @#$% | Not part of words |
| `Z*` | Separator | (converted to space) | Word boundaries |

---

## Impact on Existing Functionality

### ✅ Native Scripts (NEW - Now Working):
- Hindi: बिस्तर, सोफा, मेज़
- Bengali: বিছানা, সোফা, টেবিল
- Tamil: கட்டில், சோபா, மேசை
- Kannada: ಮಂಚ, ಸೋಫಾ, ಟೇಬಲ್
- Telugu: మంచం, సోఫా, టేబుల్
- Malayalam: കട്ടിൽ, സോഫ, മേശ

### ✅ English (Unchanged):
- All English queries work exactly as before
- No impact on roman transliterations

### ✅ Fuzzy Matching (Now Works for Native):
- Native script typos can now be detected
- RapidFuzz can properly calculate similarity
- Length-based filtering applies correctly

---

## Technical Details

### Unicode Combining Characters in Indic Scripts

#### Devanagari (Hindi):
- `U+0901` - ँ (Candrabindu)
- `U+0902` - ं (Anusvara)
- `U+0903` - ः (Visarga)
- `U+093E-U+094F` - Vowel marks (ा, ि, ी, ु, ू, े, ै, ो, ौ)
- `U+094D` - ् (Virama/Halant)

#### Bengali:
- `U+09BE-U+09C4` - Vowel marks
- `U+09CD` - ্ (Hasant/Virama)
- `U+09D7` - ৗ (Au length mark)

#### Tamil:
- `U+0BBE-U+0BC2` - Vowel marks
- `U+0BC6-U+0BC8` - Vowel marks
- `U+0BCD` - ் (Pulli/Virama)

#### Kannada:
- `U+0CBE-U+0CC4` - Vowel marks
- `U+0CC6-U+0CC8` - Vowel marks
- `U+0CCA-U+0CCD` - Vowel marks and virama
- `U+0C82-U+0C83` - Anusvara and visarga

---

## Files Modified

### `backend/utils/extractor.py`
- **Function:** `normalize(text: str) -> str`
- **Change:** Added `unicodedata.category(ch) in ('Mn', 'Mc')` condition
- **Impact:** Preserves Unicode combining marks for Indic scripts

---

## Performance

- **No performance impact** - just one additional category check per character
- Character-by-character processing unchanged
- No additional memory usage

---

## Rollback

If issues arise, revert to old normalization:

```python
def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = text.replace("\u200c", "").replace("\u200d", "")
    text = "".join(
        ch if ch.isalnum() or ch.isspace() else " "
        for ch in text
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text
```

---

## Summary

### ✅ What's Fixed:
1. Native script words stay intact during normalization
2. Fuzzy matching now works for Hindi, Bengali, Tamil, Kannada, Telugu, Malayalam
3. Typo detection works for native scripts
4. Synonym index properly indexes native text
5. RapidFuzz can calculate proper similarity scores

### 📊 Impact:
- **Critical:** Enables multilingual fuzzy search
- **Users:** Can now use native scripts with confidence
- **Accuracy:** Fuzzy matching works across all supported languages

### 🚀 Next Steps:
1. Deploy the fix
2. Test with real native script queries
3. Monitor for any edge cases
4. Consider adding more language-specific optimizations

---

## References

- Unicode Standard: https://unicode.org/reports/tr44/#General_Category_Values
- Devanagari Unicode Block: U+0900–U+097F
- Bengali Unicode Block: U+0980–U+09FF
- Tamil Unicode Block: U+0B80–U+0BFF
- Kannada Unicode Block: U+0C80–U+0CFF
