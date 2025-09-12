#!/bin/bash
# Test runner script for custom file utility filters
# Usage: ./run_tests.sh (from playbooks directory)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYBOOKS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🧪 Running Custom Filter Tests..."
echo "📁 Working directory: $PLAYBOOKS_DIR"

# Change to playbooks directory
cd "$PLAYBOOKS_DIR"

# Check if ansible.cfg exists and has filter_plugins configured
if [ ! -f "ansible.cfg" ]; then
    echo "❌ Error: ansible.cfg not found in $PLAYBOOKS_DIR"
    echo "   Please run this script from the playbooks directory or ensure ansible.cfg exists"
    exit 1
fi

if ! grep -q "filter_plugins.*filter_plugins" ansible.cfg; then
    echo "⚠️  Warning: filter_plugins may not be configured in ansible.cfg"
    echo "   Expected: filter_plugins = ./filter_plugins"
fi

# Run the test playbook
echo "🚀 Executing filter tests..."
ansible-playbook filter_plugins/tests/test_file_utils.yaml -v

echo ""
echo "✅ Filter tests completed!"
echo "📋 Test coverage:"
echo "   • file_exists filter validation"
echo "   • path_exists filter validation" 
echo "   • file_readable filter validation"
echo "   • Error handling (empty strings, null values)"
echo "   • Comparative behavior testing"
echo "   • Performance testing with file lists"
