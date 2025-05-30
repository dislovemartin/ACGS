#!/bin/bash

# ACGS-PGP Paper Compilation Script
# This script compiles the LaTeX paper with proper bibliography processing

echo "=== ACGS-PGP Paper Compilation ==="
echo "Starting compilation process..."

# Check if required files exist
if [ ! -f "acgs_pgp_main_with_figures.tex" ]; then
    echo "Error: acgs_pgp_main_with_figures.tex not found!"
    exit 1
fi

if [ ! -f "acgs_pgp_refs.bib" ]; then
    echo "Error: acgs_pgp_refs.bib not found!"
    exit 1
fi

# Step 1: First LaTeX compilation
echo "Step 1: First pdflatex compilation..."
pdflatex acgs_pgp_main_with_figures.tex

# Step 2: BibTeX processing
echo "Step 2: Processing bibliography with bibtex..."
bibtex acgs_pgp_main_with_figures

# Step 3: Second LaTeX compilation (for bibliography)
echo "Step 3: Second pdflatex compilation..."
pdflatex acgs_pgp_main_with_figures.tex

# Step 4: Third LaTeX compilation (for cross-references)
echo "Step 4: Third pdflatex compilation..."
pdflatex acgs_pgp_main_with_figures.tex

echo "=== Compilation Complete ==="

# Check if PDF was generated successfully
if [ -f "acgs_pgp_main_with_figures.pdf" ]; then
    echo "✓ PDF generated successfully: acgs_pgp_main_with_figures.pdf"
    echo "Document pages: $(pdfinfo acgs_pgp_main_with_figures.pdf 2>/dev/null | grep Pages | awk '{print $2}')"
else
    echo "✗ PDF generation failed. Check the log file for errors."
    echo "Log file: acgs_pgp_main_with_figures.log"
fi

echo ""
echo "=== Next Steps for Submission ==="
echo "1. Review the generated PDF for formatting and content"
echo "2. Create actual figure files to replace placeholder boxes"
echo "3. Complete the appendix sections with full policy examples"
echo "4. Update author information for submission (currently anonymous)"
echo "5. Check page limits and formatting requirements for target venue"
echo "6. Run final quality checks (spell check, citation verification, etc.)" 