#!/bin/bash

# AlphaEvolve-ACGS arXiv Submission Preparation Script
# This script prepares the final submission package for arXiv

echo "=== AlphaEvolve-ACGS arXiv Submission Preparation ==="
echo "Preparing submission package..."

# Create submission directory
SUBMISSION_DIR="arxiv_submission_package"
mkdir -p "$SUBMISSION_DIR"

echo "✅ Created submission directory: $SUBMISSION_DIR"

# Copy main LaTeX file
cp main.tex "$SUBMISSION_DIR/"
echo "✅ Copied main.tex"

# Copy bibliography file
cp main.bbl "$SUBMISSION_DIR/"
echo "✅ Copied main.bbl (317 references)"

# Copy figures directory
cp -r figs "$SUBMISSION_DIR/"
echo "✅ Copied figs/ directory (6 figures)"

# Copy any additional required files
if [ -f "appendix_lipschitz_estimation.tex" ]; then
    cp appendix_lipschitz_estimation.tex "$SUBMISSION_DIR/"
    echo "✅ Copied appendix file"
fi

# Create README for submission
cat > "$SUBMISSION_DIR/README.txt" << EOF
AlphaEvolve-ACGS: A Co-Evolutionary Framework for LLM-Driven Constitutional Governance in Evolutionary Computation

arXiv Preprint Submission Package

Author: Martin Honglin Lyu
ORCID: 0009-0000-6094-8416
Affiliation: Independent Researcher, Soln AI (Nvidia Inception)
Email: martin.lyu@protonmail.com

Files included:
- main.tex: Main LaTeX source file (modified for arXiv)
- main.bbl: Bibliography file with 317 references
- figs/: Directory containing 6 figures
  - Figure_1_Appeal_and_Dispute_Resolution_Workflow.png
  - Figure_2_Enhanced_Explainability_Dashboard_Mockup.png
  - Figure_3_Rule_Synthesis_Success_Rate_per_Principle.png
  - Figure_4_Constitutional_Compliance_Over_Generations.png
  - Figure_5_compliance_generations.png
  - architecture_overview.png (teaser figure)

Compilation instructions:
1. Use XeLaTeX for compilation
2. Run: xelatex main.tex
3. Process bibliography: bibtex main
4. Run XeLaTeX twice more for cross-references

arXiv categories:
- Primary: cs.AI (Artificial Intelligence)
- Secondary: cs.CY (Computers and Society)

This is a preprint currently under review for FAccT 2025.
EOF

echo "✅ Created README.txt"

# List contents of submission package
echo ""
echo "=== Submission Package Contents ==="
find "$SUBMISSION_DIR" -type f | sort

# Calculate package size
PACKAGE_SIZE=$(du -sh "$SUBMISSION_DIR" | cut -f1)
echo ""
echo "📦 Package size: $PACKAGE_SIZE"

# Create a zip file for easy upload
ZIP_NAME="AlphaEvolve-ACGS_arXiv_submission.zip"
zip -r "$ZIP_NAME" "$SUBMISSION_DIR"
echo "✅ Created zip file: $ZIP_NAME"

echo ""
echo "=== Submission Ready! ==="
echo "📁 Directory: $SUBMISSION_DIR"
echo "📦 Zip file: $ZIP_NAME"
echo ""
echo "Next steps:"
echo "1. Upload to arXiv at https://arxiv.org/submit"
echo "2. Select categories: cs.AI (primary), cs.CY (secondary)"
echo "3. Use the abstract from main.tex"
echo "4. Include keywords: AI Governance, Evolutionary Computation, Constitutional AI, etc."
echo "5. Monitor for processing and publication"
echo ""
echo "🎉 arXiv submission package is ready!"
