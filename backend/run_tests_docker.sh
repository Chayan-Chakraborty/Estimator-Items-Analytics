#!/bin/bash

# Run tests inside Docker container
# Usage: ./run_tests_docker.sh

set -e

echo "🐳 Running Fuzzy Search Tests in Docker"
echo "========================================"
echo ""

# Find the backend container
CONTAINER_NAME="voice-text-search-platform-backend-1"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Error: Container '${CONTAINER_NAME}' is not running"
    echo "   Start it with: docker compose up -d"
    exit 1
fi

echo "📦 Container: ${CONTAINER_NAME}"
echo "🧪 Running tests..."
echo ""

# Run tests in container
docker exec ${CONTAINER_NAME} python test_fuzzy_search.py

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. See output above for details."
fi

exit $EXIT_CODE
