#!/bin/bash

# Supply Chain Risk Monitor - Setup Script
# This script automates the setup process for Unix-like systems (Linux, macOS)

set -e  # Exit on error

echo "========================================"
echo "Supply Chain Risk Monitor - Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Step 1: Setup Python environment
echo ""
echo "Step 1: Setting up Python environment..."
cd index_build

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}!${NC} Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓${NC} Dependencies installed"

# Step 2: Build index
echo ""
echo "Step 2: Building index with demo data..."
python main.py

if [ ! -f "../bundle/vectors.bin" ] || [ ! -f "../bundle/meta.json" ]; then
    echo -e "${RED}Error: Index build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Index built successfully"

# Step 3: Copy bundle to extension
echo ""
echo "Step 3: Copying bundle to Chrome extension..."
cd ..
mkdir -p chrome_ext/bundle
cp bundle/vectors.bin chrome_ext/bundle/
cp bundle/meta.json chrome_ext/bundle/

if [ -f "chrome_ext/bundle/vectors.bin" ] && [ -f "chrome_ext/bundle/meta.json" ]; then
    echo -e "${GREEN}✓${NC} Bundle copied to extension"
else
    echo -e "${RED}Error: Failed to copy bundle${NC}"
    exit 1
fi

# Step 4: Display instructions
echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Open Chrome and navigate to: chrome://extensions/"
echo "2. Enable 'Developer mode' (toggle in top-right)"
echo "3. Click 'Load unpacked'"
echo "4. Select the 'chrome_ext' directory:"
echo "   $(pwd)/chrome_ext"
echo ""
echo "5. Test the extension:"
echo "   - Navigate to any page"
echo "   - Click the extension icon"
echo "   - Click 'Analyze Current Page'"
echo ""
echo "For more help, see:"
echo "  - QUICKSTART.md"
echo "  - INSTALLATION.md"
echo "  - README.md"
echo ""
echo -e "${GREEN}Happy monitoring! 🔍${NC}"

