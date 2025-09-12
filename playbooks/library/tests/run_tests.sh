#!/bin/bash

# Script to run unit tests for all custom modules

cd "$(dirname "$0")" || exit

echo "🧪 Running unit tests for custom modules..."
echo "==========================================="

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not active. Activating..."
    cd ../../.. || exit
    # shellcheck disable=SC1091 # activate script is in parent directory
    source activate || exit
    cd playbooks/library/tests || exit
fi

# Count available tests
total_tests=0
executed_tests=0
failed_tests=0

echo ""
echo "📋 Available modules for testing:"
echo "================================="

# List of modules and their tests
declare -A module_tests=(
    ["process_facts"]="test_process_facts.py"
    ["nginx_config_parser"]="test_nginx_config_parser.py"
    ["apache_config_parser"]="test_apache_config_parser.py"
    ["php_config_parser"]="test_php_config_parser.py"
)

# Check which tests exist
for module in "${!module_tests[@]}"; do
    test_file="${module_tests[$module]}"
    if [[ -f "$test_file" ]]; then
        echo "✅ $module -> $test_file"
        ((total_tests++))
    else
        echo "❌ $module -> $test_file (not found)"
    fi
done

echo ""
echo "🚀 Running found tests..."
echo "========================"

# Run process_facts tests
if [[ -f "test_process_facts.py" ]]; then
    echo ""
    echo "🧪 Testing process_facts..."
    echo "---------------------------"
    if python3 -m unittest test_process_facts.py -v; then
        ((executed_tests++))
        echo "✅ process_facts: PASSED"
    else
        ((failed_tests++))
        echo "❌ process_facts: FAILED"
    fi
fi

# Run nginx_config_parser tests
if [[ -f "test_nginx_config_parser.py" ]]; then
    echo ""
    echo "🧪 Testing nginx_config_parser..."
    echo "---------------------------------"
    if python3 -m unittest test_nginx_config_parser -v; then
        ((executed_tests++))
        echo "✅ nginx_config_parser: PASSED"
    else
        ((failed_tests++))
        echo "❌ nginx_config_parser: FAILED"
    fi
fi

# Run apache_config_parser tests (if exists)
if [[ -f "test_apache_config_parser.py" ]]; then
    echo ""
    echo "🧪 Testing apache_config_parser..."
    echo "----------------------------------"
    if python3 -m unittest test_apache_config_parser.py -v; then
        ((executed_tests++))
        echo "✅ apache_config_parser: PASSED"
    else
        ((failed_tests++))
        echo "❌ apache_config_parser: FAILED"
    fi
else
    echo ""
    echo "⚠️  test_apache_config_parser.py not found - create test needed"
fi

# Run php_config_parser tests (if exists)
if [[ -f "test_php_config_parser.py" ]]; then
    echo ""
    echo "🧪 Testing php_config_parser..."
    echo "-------------------------------"
    if python3 -m unittest test_php_config_parser.py -v; then
        ((executed_tests++))
        echo "✅ php_config_parser: PASSED"
    else
        ((failed_tests++))
        echo "❌ php_config_parser: FAILED"
    fi
else
    echo ""
    echo "⚠️  test_php_config_parser.py not found - create test needed"
fi

echo ""
echo "🔍 Checking test code quality..."
echo "================================================"

# Lint all test files
for test_file in test_*.py; do
    if [[ -f "$test_file" ]]; then
        echo "🧹 Checking $test_file..."
        python3 -m flake8 "$test_file" --ignore=E501,E203,W503,W504
    fi
done

echo ""
echo "📊 TEST SUMMARY"
echo "===================="
echo "📁 Total modules: 4 (process_facts, nginx_config_parser, apache_config_parser, php_config_parser)"
echo "✅ Tests executed: $executed_tests"
echo "❌ Tests failed: $failed_tests"
echo "⚠️  Missing tests: $((4 - total_tests))"
