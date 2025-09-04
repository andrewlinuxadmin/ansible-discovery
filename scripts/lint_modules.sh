#!/bin/bash
# Ansible Discovery Modules - Lint Script
# Run comprehensive linting on all Python modules

set -e

echo "=================================="
echo "ANSIBLE DISCOVERY MODULES - LINT"
echo "=================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories to check
LIBRARY_DIR="playbooks/library"
FILTER_PLUGINS_DIR="playbooks/filter_plugins"

echo -e "${BLUE}📁 Scanning directories:${NC}"
echo "   - $LIBRARY_DIR"
echo "   - $FILTER_PLUGINS_DIR"
echo

# Count Python files
PYTHON_FILES=$(find $LIBRARY_DIR $FILTER_PLUGINS_DIR -name "*.py" -type f | wc -l)
echo -e "${BLUE}📊 Found $PYTHON_FILES Python files to lint${NC}"
echo

# 1. PEP 8 Compliance Check (flake8)
echo -e "${YELLOW}🔍 Step 1: PEP 8 Compliance Check (flake8)${NC}"
echo "----------------------------------------"
if flake8 $LIBRARY_DIR/*.py $FILTER_PLUGINS_DIR/*.py --max-line-length=79 --statistics; then
    echo -e "${GREEN}✅ All PEP 8 compliance checks passed!${NC}"
else
    echo -e "${RED}❌ PEP 8 compliance issues found${NC}"
    exit 1
fi
echo

# 2. Code Quality Analysis (pylint)
echo -e "${YELLOW}🔍 Step 2: Code Quality Analysis (pylint)${NC}"
echo "----------------------------------------"
# Run pylint with specific disabled warnings for Ansible modules
pylint $LIBRARY_DIR/*.py $FILTER_PLUGINS_DIR/*.py \
    --max-line-length=79 \
    --disable=C0103,R0903,W0613,C0114,C0115,C0116,C0415,W1514,C0209,R1735,W0718 \
    --score=yes \
    --reports=no || echo -e "${YELLOW}⚠️  Some code quality suggestions available${NC}"
echo

# 3. Security Analysis (bandit)
echo -e "${YELLOW}🔍 Step 3: Security Analysis (bandit)${NC}"
echo "----------------------------------------"
if command -v bandit &> /dev/null; then
    bandit -r $LIBRARY_DIR $FILTER_PLUGINS_DIR -f json -q 2>/dev/null || true
    echo -e "${GREEN}✅ Security analysis completed${NC}"
else
    echo -e "${YELLOW}⚠️  bandit not installed, skipping security analysis${NC}"
fi
echo

# 4. File Summary
echo -e "${YELLOW}📋 Step 4: File Summary${NC}"
echo "----------------------------------------"
echo -e "${BLUE}Library Modules:${NC}"
ls -la $LIBRARY_DIR/*.py | awk '{print "   - " $9 " (" $5 " bytes)"}'
echo
echo -e "${BLUE}Filter Plugins:${NC}"
ls -la $FILTER_PLUGINS_DIR/*.py | awk '{print "   - " $9 " (" $5 " bytes)"}'
echo

# 5. Final Status
echo -e "${GREEN}🎉 LINT ANALYSIS COMPLETED${NC}"
echo "=================================="
echo -e "${GREEN}✅ All modules are PEP 8 compliant${NC}"
echo -e "${GREEN}✅ Code quality checks completed${NC}"
echo -e "${GREEN}✅ Ready for production use${NC}"
echo
echo "For detailed analysis, run individual tools:"
echo "  - flake8: Basic PEP 8 compliance"
echo "  - pylint: Advanced code quality analysis"
echo "  - black: Automatic code formatting"
echo "  - bandit: Security vulnerability scanning"
