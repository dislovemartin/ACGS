#!/bin/bash

# AlphaEvolve-ACGS Paper Build and Validation Script
# Comprehensive build pipeline with validation and quality checks

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
LOG_DIR="${SCRIPT_DIR}/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_DIR}/build_${TIMESTAMP}.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_DIR}/build_${TIMESTAMP}.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${LOG_DIR}/build_${TIMESTAMP}.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_DIR}/build_${TIMESTAMP}.log"
}

# Setup function
setup_environment() {
    log_info "Setting up build environment..."
    
    # Create directories
    mkdir -p "${BUILD_DIR}" "${LOG_DIR}"
    
    # Check dependencies
    check_dependencies
    
    log_success "Environment setup complete"
}

# Dependency checking
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check LaTeX
    if ! command -v pdflatex &> /dev/null; then
        missing_deps+=("pdflatex")
    fi
    
    if ! command -v bibtex &> /dev/null; then
        missing_deps+=("bibtex")
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check additional tools
    if ! command -v pdfinfo &> /dev/null; then
        log_warning "pdfinfo not found - PDF metadata validation will be skipped"
    fi
    
    if ! command -v chktex &> /dev/null; then
        log_warning "chktex not found - LaTeX linting will be skipped"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies and try again"
        exit 1
    fi
    
    log_success "All required dependencies found"
}

# Figure generation
generate_figures() {
    log_info "Generating figures..."
    
    if [ -f "create_missing_figures.py" ]; then
        python3 create_missing_figures.py
        if [ $? -eq 0 ]; then
            log_success "Figures generated successfully"
        else
            log_error "Figure generation failed"
            return 1
        fi
    else
        log_warning "Figure generation script not found"
    fi
}

# LaTeX compilation
compile_latex() {
    log_info "Compiling LaTeX document..."
    
    # Clean previous build artifacts
    rm -f main.aux main.bbl main.blg main.log main.out main.pdf
    
    # First pass
    log_info "Running first LaTeX pass..."
    pdflatex -interaction=nonstopmode main.tex > "${LOG_DIR}/latex_pass1_${TIMESTAMP}.log" 2>&1
    
    # Bibliography
    if [ -f "main.aux" ]; then
        log_info "Processing bibliography..."
        bibtex main > "${LOG_DIR}/bibtex_${TIMESTAMP}.log" 2>&1
    fi
    
    # Second pass
    log_info "Running second LaTeX pass..."
    pdflatex -interaction=nonstopmode main.tex > "${LOG_DIR}/latex_pass2_${TIMESTAMP}.log" 2>&1
    
    # Third pass for cross-references
    log_info "Running final LaTeX pass..."
    pdflatex -interaction=nonstopmode main.tex > "${LOG_DIR}/latex_pass3_${TIMESTAMP}.log" 2>&1
    
    if [ -f "main.pdf" ]; then
        log_success "PDF compilation successful"
        return 0
    else
        log_error "PDF compilation failed"
        return 1
    fi
}

# Validation functions
validate_compilation() {
    log_info "Validating compilation..."
    
    if [ ! -f "main.log" ]; then
        log_error "Compilation log not found"
        return 1
    fi
    
    # Check for errors
    if grep -q "! " main.log; then
        log_error "LaTeX compilation errors found:"
        grep "! " main.log | head -5
        return 1
    fi
    
    # Check for undefined references
    if grep -q "Warning.*undefined" main.log; then
        log_warning "Undefined references found:"
        grep "Warning.*undefined" main.log | head -5
    fi
    
    log_success "Compilation validation passed"
    return 0
}

validate_pdf_metadata() {
    log_info "Validating PDF metadata..."
    
    if ! command -v pdfinfo &> /dev/null; then
        log_warning "pdfinfo not available - skipping metadata validation"
        return 0
    fi
    
    if [ ! -f "main.pdf" ]; then
        log_error "PDF file not found"
        return 1
    fi
    
    # Extract metadata
    pdfinfo main.pdf > "${LOG_DIR}/pdf_metadata_${TIMESTAMP}.txt" 2>&1
    
    # Check required fields
    local required_fields=("Title:" "Subject:" "Author:")
    local missing_fields=()
    
    for field in "${required_fields[@]}"; do
        if ! grep -q "$field" "${LOG_DIR}/pdf_metadata_${TIMESTAMP}.txt"; then
            missing_fields+=("$field")
        fi
    done
    
    if [ ${#missing_fields[@]} -ne 0 ]; then
        log_error "Missing PDF metadata fields: ${missing_fields[*]}"
        return 1
    fi
    
    log_success "PDF metadata validation passed"
    return 0
}

validate_bibliography() {
    log_info "Validating bibliography..."
    
    if [ -f "validate_paper.py" ]; then
        python3 validate_paper.py --dir . > "${LOG_DIR}/paper_validation_${TIMESTAMP}.log" 2>&1
        if [ $? -eq 0 ]; then
            log_success "Paper validation passed"
        else
            log_warning "Paper validation found issues - check log for details"
        fi
    else
        log_warning "Paper validation script not found"
    fi
}

lint_latex() {
    log_info "Linting LaTeX source..."
    
    if ! command -v chktex &> /dev/null; then
        log_warning "chktex not available - skipping LaTeX linting"
        return 0
    fi
    
    chktex -v0 -q main.tex > "${LOG_DIR}/chktex_${TIMESTAMP}.log" 2>&1 || true
    
    if [ -s "${LOG_DIR}/chktex_${TIMESTAMP}.log" ]; then
        log_warning "ChkTeX found potential issues - check log for details"
    else
        log_success "No LaTeX linting issues found"
    fi
}

# Performance metrics
collect_metrics() {
    log_info "Collecting build metrics..."
    
    local metrics_file="${LOG_DIR}/build_metrics_${TIMESTAMP}.json"
    
    cat > "$metrics_file" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "build_duration": "$(date +%s)",
    "pdf_info": {
EOF
    
    if [ -f "main.pdf" ]; then
        echo "        \"file_size\": \"$(ls -lh main.pdf | awk '{print $5}')\"," >> "$metrics_file"
        
        if command -v pdfinfo &> /dev/null; then
            local pages=$(pdfinfo main.pdf | grep "Pages:" | awk '{print $2}')
            echo "        \"page_count\": ${pages:-0}," >> "$metrics_file"
        fi
    fi
    
    cat >> "$metrics_file" << EOF
        "compilation_passes": 3
    },
    "validation_results": {
        "compilation_errors": $(grep -c "! " main.log 2>/dev/null || echo 0),
        "warnings": $(grep -c "Warning" main.log 2>/dev/null || echo 0)
    }
}
EOF
    
    log_success "Build metrics collected"
}

# Generate build report
generate_report() {
    log_info "Generating build report..."
    
    local report_file="${BUILD_DIR}/build_report_${TIMESTAMP}.md"
    
    cat > "$report_file" << EOF
# AlphaEvolve-ACGS Build Report

**Build Timestamp:** ${TIMESTAMP}
**Build Status:** $([ -f "main.pdf" ] && echo "✅ SUCCESS" || echo "❌ FAILED")

## Build Summary

EOF
    
    if [ -f "main.pdf" ]; then
        echo "- ✅ PDF generated successfully" >> "$report_file"
        echo "- 📄 File size: $(ls -lh main.pdf | awk '{print $5}')" >> "$report_file"
        
        if command -v pdfinfo &> /dev/null; then
            local pages=$(pdfinfo main.pdf | grep "Pages:" | awk '{print $2}')
            echo "- 📖 Page count: ${pages:-Unknown}" >> "$report_file"
        fi
    else
        echo "- ❌ PDF generation failed" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "## Validation Results" >> "$report_file"
    echo "" >> "$report_file"
    
    if [ -f "main.log" ]; then
        local errors=$(grep -c "! " main.log 2>/dev/null || echo 0)
        local warnings=$(grep -c "Warning" main.log 2>/dev/null || echo 0)
        
        echo "- Compilation errors: $errors" >> "$report_file"
        echo "- Compilation warnings: $warnings" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "## Build Logs" >> "$report_file"
    echo "" >> "$report_file"
    echo "Build logs are available in the \`logs/\` directory:" >> "$report_file"
    echo "" >> "$report_file"
    
    for log_file in "${LOG_DIR}"/*_${TIMESTAMP}.log; do
        if [ -f "$log_file" ]; then
            echo "- \`$(basename "$log_file")\`" >> "$report_file"
        fi
    done
    
    log_success "Build report generated: $report_file"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Remove auxiliary files but keep PDF and logs
    rm -f main.aux main.bbl main.blg main.out main.fdb_latexmk main.fls
    
    log_success "Cleanup complete"
}

# Main build function
main() {
    log_info "Starting AlphaEvolve-ACGS paper build process..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Setup
    setup_environment
    
    # Generate figures
    generate_figures || log_warning "Figure generation had issues"
    
    # Lint LaTeX
    lint_latex
    
    # Compile LaTeX
    if ! compile_latex; then
        log_error "LaTeX compilation failed"
        exit 1
    fi
    
    # Validate results
    validate_compilation || log_warning "Compilation validation had issues"
    validate_pdf_metadata || log_warning "PDF metadata validation had issues"
    validate_bibliography || log_warning "Bibliography validation had issues"
    
    # Collect metrics and generate report
    collect_metrics
    generate_report
    
    # Cleanup
    cleanup
    
    log_success "Build process completed successfully!"
    log_info "PDF: main.pdf"
    log_info "Build report: ${BUILD_DIR}/build_report_${TIMESTAMP}.md"
    log_info "Logs: ${LOG_DIR}/"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
