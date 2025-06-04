# TAPS Submission Preparation Guide for FAccT 2025

## Overview
This guide helps prepare your AlphaEvolve-ACGS paper for submission to the ACM TAPS (The ACM Production System) for FAccT 2025.

## Current Status ✅
- ✅ Single `\documentclass{acmart}` command
- ✅ Proper figure organization in `figs/` directory
- ✅ Bibliography file (`AlphaEvolve-ACGS.bib`)
- ✅ ACM conference information configured
- ✅ All packages appear to be ACM-approved
- ✅ ORCID ID added (0009-0000-6094-8416)

## Critical Actions Required Before TAPS Submission

### 1. **COMPLETE ACM RIGHTS FORM FIRST** 🚨
**IMPORTANT**: You MUST complete the ACM rights form before submitting to TAPS. This will provide you with:
- Exact copyright commands
- Actual DOI
- Actual ISBN
- Any additional required commands

### 2. **Update Rights Commands**
Replace the placeholder commands in `main.tex` lines 89-101 with the actual commands from your rights form:

```latex
% CURRENT PLACEHOLDERS - REPLACE WITH ACTUAL COMMANDS:
\copyrightyear{2025}
\acmYear{2025}
\setcopyright{rightsretained} % REPLACE with actual setting
\acmDOI{10.1145/XXXXXXX.XXXXXXX} % REPLACE with actual DOI
\acmISBN{978-1-4503-XXXX-X/25/10} % REPLACE with actual ISBN
```

### 3. **Verify Package Compatibility**
All packages in your document appear to be ACM-approved:
- ✅ `ifxetex`, `fontspec`, `inputenc`, `fontenc`, `lmodern`
- ✅ `amssymb`, `latexsym`
- ✅ `multirow`, `array`, `tabularx`, `booktabs`
- ✅ `algorithm`, `algpseudocode`
- ✅ `listings`
- ✅ `xurl`
- ✅ `enumitem`
- ✅ `cleveref`
- ✅ `xcolor`

### 4. **File Naming Requirements**
Ensure all filenames follow TAPS requirements (letters, numbers, dash, underscore only):
- ✅ `main.tex` - Good
- ✅ `AlphaEvolve-ACGS.bib` - Good
- ✅ Figure files in `figs/` - Check individual files

### 5. **Create TAPS ZIP File**
The ZIP file MUST be named exactly as instructed by TAPS:
Format: `eventname-submissionID.zip`
Example: `facct25-123.zip`

**ZIP Structure Required:**
```
facct25-[YOUR_SUBMISSION_ID].zip
├── source/
│   ├── main.tex
│   ├── AlphaEvolve-ACGS.bib
│   └── figs/
│       ├── architecture_overview.png
│       ├── appeal_workflow.png
│       ├── explainability_dashboard.png
│       └── [other figures]
└── pdf/ (optional)
    └── main.pdf
```

## TAPS Submission Checklist

### Pre-Submission
- [ ] Complete ACM rights form
- [ ] Update rights commands in LaTeX source
- [ ] Verify all figures are referenced and exist
- [ ] Check bibliography compiles without errors
- [ ] Ensure document compiles successfully
- [ ] Verify all filenames use only allowed characters

### ZIP File Creation
- [ ] Create `source/` folder
- [ ] Copy `main.tex` to `source/`
- [ ] Copy `AlphaEvolve-ACGS.bib` to `source/`
- [ ] Copy `figs/` folder to `source/`
- [ ] Optionally create `pdf/` folder with compiled PDF
- [ ] Name ZIP file exactly as instructed by TAPS
- [ ] Verify ZIP is under 10MB (use FTP if larger)

### Submission
- [ ] Upload ZIP via TAPS interface (if <10MB)
- [ ] Use FTP upload (if ≥10MB)
- [ ] Wait for TAPS processing confirmation email
- [ ] Review generated PDF and HTML when ready
- [ ] Approve or reject and resubmit if needed

## Common TAPS Validation Errors to Avoid

1. **Missing Rights Commands**: Ensure all commands from rights form are included
2. **Invalid LaTeX Packages**: All packages in your document are approved
3. **Missing Figures**: All figures referenced in text must be in ZIP
4. **Incorrect Template**: You're using `acmart` correctly
5. **Document Not Validated**: Your document should compile without errors

## Quick Commands for ZIP Creation

```bash
# Navigate to your paper directory
cd docs/research/AlphaEvolve-ACGS_Integration_System/

# Create TAPS directory structure
mkdir -p taps-submission/source
mkdir -p taps-submission/pdf

# Copy required files
cp main.tex taps-submission/source/
cp AlphaEvolve-ACGS.bib taps-submission/source/
cp -r figs/ taps-submission/source/
cp main.pdf taps-submission/pdf/ # if you have a compiled PDF

# Create ZIP (replace with your actual submission ID)
cd taps-submission
zip -r facct25-YOUR_SUBMISSION_ID.zip source/ pdf/
```

## Next Steps

1. **Complete the ACM rights form** - This is your first priority
2. **Update the LaTeX source** with actual rights commands
3. **Test compilation** to ensure everything works
4. **Create the ZIP file** following the exact naming convention
5. **Submit to TAPS** and monitor for validation results

## Support

- TAPS emails come from: `tapsadmin@aptaracorp.awsapps.com`
- Ensure this email address is not blocked
- TAPS will provide specific instructions including exact ZIP filename
- Review TAPS validation messages carefully if errors occur

## Document Status
- **LaTeX Source**: Ready (pending rights commands update)
- **Bibliography**: Complete
- **Figures**: Present and properly referenced
- **Package Compatibility**: Verified
- **Rights Commands**: **NEEDS UPDATE FROM RIGHTS FORM**
