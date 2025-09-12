#!/bin/bash
# Test MongoDB Queries - Example Usage Script
# ==========================================

set -e

echo "🧪 Testing MongoDB Query Validation Tool"
echo "========================================"

# Change to project directory
cd "$(dirname "$0")"

# Check if enhanced-queries.html exists
if [ ! -f "enhanced-queries.html" ]; then
    echo "❌ Error: enhanced-queries.html not found"
    echo "Please ensure the file exists in the current directory"
    exit 1
fi

# Check if MongoDB proxy is running
echo "🔍 Checking MongoDB proxy availability..."
if ! curl -s http://localhost:45678/healthz > /dev/null 2>&1; then
    echo "❌ Error: MongoDB proxy not available at localhost:45678"
    echo "Please start the MongoDB proxy first:"
    echo "   cd mongodb-proxy && python mongodb-proxy.py"
    exit 1
fi

echo "✅ MongoDB proxy is available"
echo ""

# Run the query test with different options based on arguments
if [ "$1" = "--quick" ]; then
    echo "🚀 Running quick test (first 5 queries only)..."
    python3 test_all_queries.py --verbose | head -50
elif [ "$1" = "--full" ]; then
    echo "🔍 Running full test with detailed output..."
    python3 test_all_queries.py --verbose --output "query_test_report_$(date +%Y%m%d_%H%M%S).txt"
else
    echo "🧪 Running standard test..."
    echo "Usage options:"
    echo "  ./test_queries_example.sh --quick   # Quick test (first few queries)"
    echo "  ./test_queries_example.sh --full    # Full test with report file"
    echo ""
    python3 test_all_queries.py
fi

echo ""
echo "✅ Test completed!"
echo ""
echo "💡 Additional usage examples:"
echo "   python3 test_all_queries.py --help"
echo "   python3 test_all_queries.py --verbose"
echo "   python3 test_all_queries.py --host localhost --port 45678"
echo "   python3 test_all_queries.py --output report.txt"
