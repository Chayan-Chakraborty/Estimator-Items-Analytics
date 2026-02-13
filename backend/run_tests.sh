#!/bin/bash

# Test runner script for fuzzy search tests
# Usage: ./run_tests.sh

set -e

echo "🧪 Running Fuzzy Search Tests"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -f "test_fuzzy_search.py" ]; then
    echo "❌ Error: test_fuzzy_search.py not found"
    echo "   Please run this script from the backend directory"
    exit 1
fi

# Run the tests
python test_fuzzy_search.py

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. See output above for details."
fi

exit $EXIT_CODE
