#!/bin/bash

# TAPS Submission Preparation Script for FAccT 2025
# This script helps prepare your LaTeX document for ACM TAPS submission

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PAPER_DIR="$(pwd)"
TAPS_DIR="$PAPER_DIR/taps-submission"
SOURCE_DIR="$TAPS_DIR/source"
PDF_DIR="$TAPS_DIR/pdf"

echo -e "${BLUE}=== FAccT 2025 TAPS Submission Preparation ===${NC}"
echo "Paper directory: $PAPER_DIR"
echo

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}ERROR: Required file not found: $1${NC}"
        exit 1
    fi
}

# Function to validate filename
validate_filename() {
    local filename="$1"
    if [[ ! "$filename" =~ ^[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+$ ]]; then
        echo -e "${YELLOW}WARNING: Filename '$filename' may not comply with TAPS requirements${NC}"
        echo "TAPS requires filenames to contain only letters, numbers, dash (-), and underscore (_)"
    fi
}

# Step 1: Check required files
echo -e "${BLUE}Step 1: Checking required files...${NC}"
check_file "main.tex"
check_file "AlphaEvolve-ACGS.bib"
check_file "figs/architecture_overview.png"

echo -e "${GREEN}✓ Required files found${NC}"
echo

# Step 2: Validate filenames
echo -e "${BLUE}Step 2: Validating filenames...${NC}"
validate_filename "main.tex"
validate_filename "AlphaEvolve-ACGS.bib"

# Check figure filenames
if [ -d "figs" ]; then
    for fig in figs/*; do
        if [ -f "$fig" ]; then
            validate_filename "$(basename "$fig")"
        fi
    done
fi

echo -e "${GREEN}✓ Filename validation complete${NC}"
echo

# Step 3: Check for rights commands
echo -e "${BLUE}Step 3: Checking rights commands...${NC}"
if grep -q "REPLACE.*rights form" main.tex; then
    echo -e "${RED}WARNING: Placeholder rights commands detected!${NC}"
    echo "You MUST complete the ACM rights form and update the following commands:"
    echo "- \\setcopyright{...}"
    echo "- \\acmDOI{...}"
    echo "- \\acmISBN{...}"
    echo "- Any additional commands from your rights form"
    echo
    read -p "Have you completed the ACM rights form and updated the commands? (y/N): " rights_updated
    if [[ ! "$rights_updated" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Please complete the rights form first, then run this script again.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Rights commands appear to be updated${NC}"
fi
echo

# Step 4: Test compilation
echo -e "${BLUE}Step 4: Testing LaTeX compilation...${NC}"
if command -v xelatex >/dev/null 2>&1; then
    echo "Testing compilation with xelatex..."
    if xelatex -interaction=nonstopmode main.tex >/dev/null 2>&1; then
        echo -e "${GREEN}✓ LaTeX compilation successful${NC}"
    else
        echo -e "${RED}ERROR: LaTeX compilation failed${NC}"
        echo "Please fix compilation errors before proceeding."
        exit 1
    fi
else
    echo -e "${YELLOW}WARNING: xelatex not found. Please ensure your document compiles.${NC}"
fi
echo

# Step 5: Get submission ID
echo -e "${BLUE}Step 5: TAPS submission information...${NC}"
echo "TAPS will provide you with specific instructions including:"
echo "- Event name (likely 'facct25')"
echo "- Your submission ID"
echo "- Exact ZIP filename format"
echo
read -p "Enter your submission ID (or press Enter to use 'SUBMISSION_ID'): " submission_id
if [ -z "$submission_id" ]; then
    submission_id="SUBMISSION_ID"
    echo -e "${YELLOW}Using placeholder: $submission_id${NC}"
fi

ZIP_NAME="facct25-${submission_id}.zip"
echo "ZIP file will be named: $ZIP_NAME"
echo

# Step 6: Create TAPS directory structure
echo -e "${BLUE}Step 6: Creating TAPS directory structure...${NC}"
rm -rf "$TAPS_DIR"
mkdir -p "$SOURCE_DIR"
mkdir -p "$PDF_DIR"

echo -e "${GREEN}✓ Directory structure created${NC}"
echo

# Step 7: Copy files
echo -e "${BLUE}Step 7: Copying files...${NC}"

# Copy main files
cp main.tex "$SOURCE_DIR/"
cp AlphaEvolve-ACGS.bib "$SOURCE_DIR/"

# Copy figures directory
if [ -d "figs" ]; then
    cp -r figs/ "$SOURCE_DIR/"
    echo "✓ Copied figures directory"
fi

# Copy PDF if it exists
if [ -f "main.pdf" ]; then
    cp main.pdf "$PDF_DIR/"
    echo "✓ Copied PDF file"
else
    echo -e "${YELLOW}Note: No PDF file found. TAPS will generate one.${NC}"
fi

echo -e "${GREEN}✓ Files copied successfully${NC}"
echo

# Step 8: Create ZIP file
echo -e "${BLUE}Step 8: Creating ZIP file...${NC}"
cd "$TAPS_DIR"

if command -v zip >/dev/null 2>&1; then
    zip -r "$ZIP_NAME" source/ pdf/ >/dev/null 2>&1
    
    # Check ZIP size
    zip_size=$(stat -f%z "$ZIP_NAME" 2>/dev/null || stat -c%s "$ZIP_NAME" 2>/dev/null || echo "unknown")
    if [ "$zip_size" != "unknown" ]; then
        zip_size_mb=$((zip_size / 1024 / 1024))
        echo "ZIP file size: ${zip_size_mb}MB"
        
        if [ "$zip_size_mb" -ge 10 ]; then
            echo -e "${YELLOW}WARNING: ZIP file is ≥10MB. You must use FTP upload to TAPS.${NC}"
        else
            echo -e "${GREEN}✓ ZIP file size is <10MB. You can use the web uploader.${NC}"
        fi
    fi
    
    echo -e "${GREEN}✓ ZIP file created: $ZIP_NAME${NC}"
else
    echo -e "${RED}ERROR: zip command not found. Please install zip utility.${NC}"
    exit 1
fi

cd "$PAPER_DIR"
echo

# Step 9: Final checklist
echo -e "${BLUE}Step 9: Final submission checklist...${NC}"
echo "Before submitting to TAPS, verify:"
echo "□ ACM rights form completed"
echo "□ Rights commands updated in LaTeX source"
echo "□ Document compiles without errors"
echo "□ All figures are included and referenced"
echo "□ ZIP file named exactly as instructed by TAPS"
echo "□ Email from tapsadmin@aptaracorp.awsapps.com is not blocked"
echo

echo -e "${GREEN}=== TAPS Preparation Complete ===${NC}"
echo "Your submission files are ready in: $TAPS_DIR"
echo "ZIP file: $TAPS_DIR/$ZIP_NAME"
echo
echo "Next steps:"
echo "1. Submit the ZIP file to TAPS (web upload if <10MB, FTP if ≥10MB)"
echo "2. Wait for TAPS processing confirmation email"
echo "3. Review generated PDF and HTML when ready"
echo "4. Approve or reject and resubmit if needed"
echo
echo -e "${BLUE}Good luck with your FAccT 2025 submission!${NC}"
