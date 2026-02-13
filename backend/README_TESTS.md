# Fuzzy Search Testing

This directory contains test files for the fuzzy search functionality.

## Test Files

### `test_fuzzy_search.py`
Comprehensive test suite for the `extract_items_with_identifiers_from_query_fuzzy` function.

## Running Tests

### Method 1: Direct Python Execution

```bash
cd /Users/chayanchakraborty/Documents/python_new_dir/voice-text-search-platform/backend
python test_fuzzy_search.py
```

### Method 2: Using pytest (if installed)

```bash
cd /Users/chayanchakraborty/Documents/python_new_dir/voice-text-search-platform/backend
pytest test_fuzzy_search.py -v
```

### Method 3: Run in Docker Container

```bash
docker exec -it voice-text-search-platform-backend-1 python test_fuzzy_search.py
```

## Test Coverage

The test suite covers:

1. **Exact Match Testing**
   - Tests exact item name matches
   - Examples: "bed", "wardrobe", "sofa"

2. **Fuzzy Typo Matching**
   - Tests common typos and misspellings
   - Examples: "wadro" → "wardrobe", "tabel" → "table"

3. **Partial Matches**
   - Tests substring matching
   - Examples: "ward" → "wardrobe", "tab" → "table"

4. **Cutoff Threshold Testing**
   - Tests different similarity thresholds (0.5 to 0.95)
   - Shows how strictness affects results

5. **Multi-Word Queries**
   - Tests phrase matching
   - Examples: "dining table", "study table"

6. **Edge Cases**
   - Empty queries
   - Whitespace-only queries
   - Non-existent items
   - Very short queries
   - Special characters

7. **Case Insensitivity**
   - Tests uppercase, lowercase, and mixed case
   - Examples: "BED", "Wardrobe", "SoFa"

8. **Comma-Separated Queries**
   - Tests multiple item queries
   - Examples: "bed, cot", "wardrobe, almirah"

9. **Strict vs Lenient Matching**
   - High cutoff (0.9): Stricter matching, fewer false positives
   - Low cutoff (0.5): More lenient, catches more variations

10. **Identifier Validation**
    - Ensures identifiers are correctly returned

## Expected Output

The test suite will print detailed results for each test, including:
- Query text
- Cutoff threshold used
- Number of items found
- Item names and their identifiers
- Pass/fail status for each test

### Example Output:

```
================================================================================
TEST: Fuzzy Matching - Typos
================================================================================

Query: 'wadro' (cutoff: 0.68)
Found 1 item(s):
  - wardrobe [WARDROBE_ITM_NW]

✅ PASSED: test_fuzzy_typos

================================================================================
TEST SUMMARY
================================================================================
Total: 11
✅ Passed: 11
❌ Failed: 0
================================================================================
```

## Customizing Tests

### Adding New Test Cases

Add new test cases to existing functions:

```python
def test_fuzzy_typos():
    test_cases = [
        ("wadro", "wardrobe"),
        ("your_typo", "expected_item"),  # Add here
    ]
```

### Testing Custom Cutoff Values

```python
result = extract_items_with_identifiers_from_query_fuzzy(
    "wadro", 
    fuzzy_cutoff=0.75  # Adjust threshold
)
```

## Troubleshooting

### ImportError: No module named 'services'

Make sure you're running from the `backend` directory:
```bash
cd /Users/chayanchakraborty/Documents/python_new_dir/voice-text-search-platform/backend
```

### No items found in tests

Ensure that:
1. `resources/items_with_identifiers.json` exists and is populated
2. The application has been initialized properly
3. Docker containers are running (if testing in Docker)

## Integration with CI/CD

To integrate with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run fuzzy search tests
  run: |
    cd backend
    python test_fuzzy_search.py
```

## Performance Testing

To test performance with large datasets, modify the test to measure execution time:

```python
import time

start = time.time()
result = extract_items_with_identifiers_from_query_fuzzy("query")
elapsed = time.time() - start
print(f"Execution time: {elapsed:.3f}s")
```
