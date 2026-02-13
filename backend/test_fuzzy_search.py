"""
Test suite for extract_items_with_identifiers_from_query_fuzzy function

This file tests the fuzzy search functionality for item extraction with various scenarios:
- Exact matches
- Fuzzy matches (typos and misspellings)
- Partial matches
- Different similarity thresholds
- Edge cases

Run with:
    python test_fuzzy_search.py
    
Or with pytest:
    pytest test_fuzzy_search.py -v
"""

import sys
import os

# Add parent directory to path to import from services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.itemService import extract_items_with_identifiers_from_query_fuzzy


def print_test_header(test_name):
    """Print a formatted test header"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)


def print_result(query, result, cutoff=0.68):
    """Print formatted test result"""
    print(f"\nQuery: '{query}' (cutoff: {cutoff})")
    print(f"Found {len(result.data)} item(s):")
    for item in result.data:
        identifiers_str = ", ".join(item.identifiers) if item.identifiers else "No identifiers"
        print(f"  - {item.itemName} [{identifiers_str}]")


def test_exact_match():
    """Test exact item name matching"""
    print_test_header("Exact Match")
    
    test_cases = [
        "bed",
        "wardrobe",
        "sofa",
        "dining table",
    ]
    
    for query in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query)
        print_result(query, result)
        assert len(result.data) > 0, f"Expected results for '{query}'"


def test_fuzzy_typos():
    """Test fuzzy matching with common typos"""
    print_test_header("Fuzzy Matching - Typos")
    
    test_cases = [
        ("wadro", "wardrobe"),      # Missing letters
        ("wardob", "wardrobe"),     # Missing last letter
        ("wardrob", "wardrobe"),    # Missing last letter
        ("bedd", "bed"),            # Extra letter
        ("sofaa", "sofa"),          # Extra letter
        ("tabel", "table"),         # Swapped letters
        ("wadrobe", "wardrobe"),    # Missing letter in middle
    ]
    
    for query, expected_item in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query)
        print_result(query, result)
        
        # Check if expected item is in results
        item_names = [item.itemName.lower() for item in result.data]
        assert any(expected_item.lower() in name for name in item_names), \
            f"Expected '{expected_item}' in results for query '{query}', got: {item_names}"


def test_partial_matches():
    """Test partial word matching"""
    print_test_header("Partial Matches")
    
    test_cases = [
        "ward",      # Should match "wardrobe"
        "tab",       # Should match "table"
        "sof",       # Should match "sofa"
        "dini",      # Should match "dining table"
    ]
    
    for query in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query)
        print_result(query, result)
        assert len(result.data) > 0, f"Expected results for partial match '{query}'"


def test_cutoff_threshold():
    """Test different similarity cutoff thresholds"""
    print_test_header("Cutoff Threshold Testing")
    
    query = "wadrob"  # Typo for "wardrobe"
    
    cutoffs = [0.5, 0.68, 0.75, 0.85, 0.95]
    
    for cutoff in cutoffs:
        result = extract_items_with_identifiers_from_query_fuzzy(query, fuzzy_cutoff=cutoff)
        print_result(query, result, cutoff)
        print(f"    → Strictness: {'High' if cutoff > 0.8 else 'Medium' if cutoff > 0.7 else 'Low'}")


def test_multi_word_queries():
    """Test queries with multiple words"""
    print_test_header("Multi-Word Queries")
    
    test_cases = [
        "dining table",
        "study table",
        "sofa set",
        "center table",
        "coffee table",
    ]
    
    for query in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query)
        print_result(query, result)
        # Multi-word queries should ideally return exact phrase matches


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print_test_header("Edge Cases")
    
    # Empty query
    result = extract_items_with_identifiers_from_query_fuzzy("")
    print_result("(empty string)", result)
    assert len(result.data) == 0, "Expected no results for empty query"
    
    # Whitespace only
    result = extract_items_with_identifiers_from_query_fuzzy("   ")
    print_result("(whitespace only)", result)
    assert len(result.data) == 0, "Expected no results for whitespace-only query"
    
    # Non-existent item
    result = extract_items_with_identifiers_from_query_fuzzy("xyzabc123nonexistent")
    print_result("xyzabc123nonexistent", result)
    print("    → Expected few or no results for non-existent item")
    
    # Very short query
    result = extract_items_with_identifiers_from_query_fuzzy("be")
    print_result("be", result)
    # Short queries might return multiple matches
    
    # Special characters
    result = extract_items_with_identifiers_from_query_fuzzy("bed@#$")
    print_result("bed@#$", result)


def test_case_insensitivity():
    """Test case-insensitive matching"""
    print_test_header("Case Insensitivity")
    
    test_cases = [
        "BED",
        "Wardrobe",
        "DINING TABLE",
        "SoFa",
    ]
    
    for query in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query)
        print_result(query, result)
        assert len(result.data) > 0, f"Expected results for '{query}'"


def test_comma_separated_queries():
    """Test comma-separated item queries"""
    print_test_header("Comma-Separated Queries")
    
    test_cases = [
        "bed, cot",
        "wardrobe, almirah",
        "table, desk",
    ]
    
    for query in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query)
        print_result(query, result)


def test_high_similarity_strict():
    """Test with high similarity threshold (stricter matching)"""
    print_test_header("High Similarity (Strict)")
    
    test_cases = [
        ("bed", 0.9),
        ("wadro", 0.9),      # Should fail with high cutoff
        ("wardrobe", 0.9),   # Should pass
        ("tab", 0.9),        # Might fail with high cutoff
    ]
    
    for query, cutoff in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query, fuzzy_cutoff=cutoff)
        print_result(query, result, cutoff)


def test_low_similarity_lenient():
    """Test with low similarity threshold (more lenient matching)"""
    print_test_header("Low Similarity (Lenient)")
    
    test_cases = [
        ("wrd", 0.5),        # Very fuzzy match for "wardrobe"
        ("bd", 0.5),         # Very fuzzy match for "bed"
        ("tb", 0.5),         # Very fuzzy match for "table"
    ]
    
    for query, cutoff in test_cases:
        result = extract_items_with_identifiers_from_query_fuzzy(query, fuzzy_cutoff=cutoff)
        print_result(query, result, cutoff)
        print(f"    → Lenient matching may return many results")


def test_identifiers_present():
    """Test that identifiers are returned correctly"""
    print_test_header("Identifier Validation")
    
    result = extract_items_with_identifiers_from_query_fuzzy("bed")
    print_result("bed", result)
    
    if result.data:
        for item in result.data:
            print(f"\n  Item: {item.itemName}")
            print(f"  Identifiers: {item.identifiers}")
            print(f"  Has identifiers: {len(item.identifiers) > 0}")


def run_all_tests():
    """Run all test functions"""
    print("\n" + "🎯"*40)
    print("FUZZY SEARCH TEST SUITE")
    print("🎯"*40)
    
    test_functions = [
        test_exact_match,
        test_fuzzy_typos,
        test_partial_matches,
        test_cutoff_threshold,
        test_multi_word_queries,
        test_edge_cases,
        test_case_insensitivity,
        test_comma_separated_queries,
        test_high_similarity_strict,
        test_low_similarity_lenient,
        test_identifiers_present,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
            print(f"\n✅ PASSED: {test_func.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"\n❌ FAILED: {test_func.__name__}")
            print(f"   Error: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ ERROR: {test_func.__name__}")
            print(f"   Error: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
