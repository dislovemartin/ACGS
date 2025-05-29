# ACGS-PGP Paper Manual Compilation Guide

This guide provides step-by-step instructions for compiling the ACGS-PGP paper manually.

## Prerequisites

You'll need:

1. **LaTeX Distribution**: TeX Live (Linux/Mac) or MiKTeX (Windows)
2. **Image Conversion Tool**: One of the following:
   - Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`)
   - Draw.io Desktop or web version
   - Any vector graphics editor (Inkscape, Adobe Illustrator, etc.)

## Step 1: Create Figures

### Option A: Using Mermaid CLI (Recommended)

```bash
# Install Mermaid CLI if not already installed
npm install -g @mermaid-js/mermaid-cli

# Create figures directory
mkdir -p figures

# Convert diagrams to images
mmdc -i figure1_c4_diagram.mmd -o figures/figure1_c4_architecture.png -w 1200 -H 800 --theme neutral
mmdc -i figure2_policy_flowchart.mmd -o figures/figure2_policy_flowchart.png -w 1400 -H 1000 --theme neutral
```

### Option B: Using Draw.io (Alternative)

1. Open [app.diagrams.net](https://app.diagrams.net) in your browser
2. Copy the content from `figure1_c4_diagram.mmd` and manually recreate as a diagram
3. Export as PNG (1200x800 pixels for Figure 1, 1400x1000 for Figure 2)
4. Save as `figures/figure1_c4_architecture.png` and `figures/figure2_policy_flowchart.png`

### Option C: Use Placeholder Images (Quick Start)

If you want to compile quickly without proper figures:

```bash
mkdir -p figures
# Create placeholder images (requires ImageMagick)
convert -size 1200x800 xc:lightgray -pointsize 48 -gravity center \
        -annotate +0+0 "Figure 1: C4 Architecture\n(Placeholder)" \
        figures/figure1_c4_architecture.png

convert -size 1400x1000 xc:lightblue -pointsize 48 -gravity center \
        -annotate +0+0 "Figure 2: Policy Flowchart\n(Placeholder)" \
        figures/figure2_policy_flowchart.png
```

## Step 2: Update LaTeX File

Create a copy of the main file with figure inclusions:

```bash
cp acgs_pgp_main.tex acgs_pgp_main_with_figures.tex
```

Then manually edit `acgs_pgp_main_with_figures.tex` to replace the placeholder boxes with actual figure inclusions:

### For Figure 1 (around line 370):

Replace this block:

```latex
\fbox{\begin{minipage}{0.9\columnwidth}
  \centering
  \vspace{2cm}
  \textbf{Figure 1: Conceptual C4 Level 2 Container Diagram of the ACGS-PGP Framework.}
  \textit{(Detailed C4 diagrams are in Appendix~\ref{app:architecture}.)}
  \vspace{2cm}
\end{minipage}}
```

With:

```latex
\includegraphics[width=0.9\columnwidth]{figures/figure1_c4_architecture.png}
```

### For Figure 2 (around line 380):

Replace this block:

```latex
\fbox{\begin{minipage}{0.9\columnwidth}
  \centering
  \vspace{2cm}
  \textbf{Figure 2: Conceptual Flowchart of Policy Compilation and Enforcement within ACGS-PGP.}
  \vspace{2cm}
\end{minipage}}
```

With:

```latex
\includegraphics[width=0.9\columnwidth]{figures/figure2_policy_flowchart.png}
```

## Step 3: Compile the Document

Run the following commands in sequence:

```bash
# First pass - generates auxiliary files and identifies citations
pdflatex acgs_pgp_main_with_figures.tex

# Process bibliography
bibtex acgs_pgp_main_with_figures

# Second pass - includes bibliography
pdflatex acgs_pgp_main_with_figures.tex

# Third pass - resolves all cross-references
pdflatex acgs_pgp_main_with_figures.tex
```

## Step 4: Check Output

Your final PDF should be: `acgs_pgp_main_with_figures.pdf`

### Common Issues and Solutions

**Issue**: "File not found: figures/figure1_c4_architecture.png"

- **Solution**: Ensure the figures directory exists and contains the image files

**Issue**: Citations showing as "?" in the PDF

- **Solution**: Make sure `acgs_pgp_refs.bib` is in the same directory and re-run the compilation sequence

**Issue**: Cross-references showing as "??"

- **Solution**: Run pdflatex one more time to resolve all references

**Issue**: Package not found errors

- **Solution**: Install missing LaTeX packages through your TeX distribution's package manager

## Step 5: Quality Check

Before submission, verify:

1. **All figures display correctly** - no broken image links
2. **All citations are resolved** - no "?" in the bibliography
3. **All cross-references work** - section, table, and figure references
4. **Page count is reasonable** - typical conference papers are 8-12 pages
5. **No overfull hbox warnings** - text doesn't exceed margins

## File Structure After Compilation

```
Paper/
├── acgs_pgp_main.tex                 # Original LaTeX file
├── acgs_pgp_main_with_figures.tex    # Modified with figures
├── acgs_pgp_main_with_figures.pdf    # Final output PDF
├── acgs_pgp_refs.bib                 # Bibliography file
├── figure1_c4_diagram.mmd            # Mermaid source for Figure 1
├── figure2_policy_flowchart.mmd      # Mermaid source for Figure 2
├── figures/
│   ├── figure1_c4_architecture.png   # Figure 1 image
│   └── figure2_policy_flowchart.png  # Figure 2 image
├── compile_paper.sh                  # Automated compilation script
└── manual_compilation_guide.md       # This guide
```

## Submission Checklist

- [ ] PDF compiles without errors
- [ ] All figures are high-quality and readable
- [ ] Author information is complete and accurate
- [ ] Conference details are updated for actual submission
- [ ] Abstract is within word limit (typically 250 words)
- [ ] Bibliography has at least 25-30 high-quality references
- [ ] All placeholder URLs in bibliography are replaced with actual links
- [ ] Document follows conference formatting guidelines
- [ ] Appendices are complete and referenced properly
- [ ] No "TODO" or placeholder text remains

## Next Steps

1. **Proofread thoroughly** - Check for typos, grammatical errors, and clarity
2. **Verify novelty claims** - Ensure all claimed contributions are properly supported
3. **Update bibliography** - Replace placeholder references with actual sources
4. **Check conference requirements** - Page limits, formatting, submission system
5. **Prepare supplementary materials** if required by the conference

Your ACGS-PGP paper is now ready for final review and submission!
