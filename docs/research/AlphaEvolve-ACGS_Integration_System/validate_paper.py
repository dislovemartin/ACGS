#!/usr/bin/env python3
"""
Comprehensive validation script for the AlphaEvolve-ACGS paper.
Validates bibliography, cross-references, figures, and metadata.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple

class PaperValidator:
    def __init__(self, paper_dir: str = "."):
        self.paper_dir = Path(paper_dir)
        self.main_tex = self.paper_dir / "main.tex"
        self.main_bib = self.paper_dir / "main.bib"
        self.main_pdf = self.paper_dir / "main.pdf"
        self.main_log = self.paper_dir / "main.log"
        
        self.errors = []
        self.warnings = []
        self.info = []
        
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Starting comprehensive paper validation...")
        
        success = True
        success &= self.validate_file_structure()
        success &= self.validate_bibliography()
        success &= self.validate_cross_references()
        success &= self.validate_figures()
        success &= self.validate_pdf_metadata()
        success &= self.validate_compilation()
        
        self.print_summary()
        return success
        
    def validate_file_structure(self) -> bool:
        """Validate required files exist."""
        print("\n📁 Validating file structure...")
        
        required_files = [
            self.main_tex,
            self.main_bib,
        ]
        
        missing_files = [f for f in required_files if not f.exists()]
        
        if missing_files:
            for f in missing_files:
                self.errors.append(f"Missing required file: {f}")
            return False
            
        self.info.append("All required files present")
        return True
        
    def validate_bibliography(self) -> bool:
        """Validate bibliography integrity."""
        print("\n📚 Validating bibliography...")
        
        if not self.main_bib.exists():
            self.errors.append("Bibliography file main.bib not found")
            return False
            
        # Extract citations from main.tex
        tex_content = self.main_tex.read_text(encoding='utf-8')
        citations = set(re.findall(r'\\cite[tp]?\{([^}]+)\}', tex_content))
        
        # Flatten citation lists (handle multiple citations in one command)
        all_citations = set()
        for citation_group in citations:
            all_citations.update(c.strip() for c in citation_group.split(','))
        
        # Extract bibliography entries
        bib_content = self.main_bib.read_text(encoding='utf-8')
        bib_entries = set(re.findall(r'@\w+\{([^,]+),', bib_content))
        
        # Check for missing bibliography entries
        missing_entries = all_citations - bib_entries
        if missing_entries:
            for entry in missing_entries:
                self.errors.append(f"Citation '{entry}' not found in bibliography")
                
        # Check for unused bibliography entries
        unused_entries = bib_entries - all_citations
        if unused_entries:
            for entry in unused_entries:
                self.warnings.append(f"Bibliography entry '{entry}' not cited")
                
        self.info.append(f"Found {len(all_citations)} citations and {len(bib_entries)} bibliography entries")
        
        return len(missing_entries) == 0
        
    def validate_cross_references(self) -> bool:
        """Validate internal cross-references."""
        print("\n🔗 Validating cross-references...")
        
        tex_content = self.main_tex.read_text(encoding='utf-8')
        
        # Extract labels (standalone and within environments like lstlisting)
        standalone_labels = set(re.findall(r'\\label\{([^}]+)\}', tex_content))
        # More flexible regex for lstlisting labels
        lstlisting_labels = set(re.findall(r'label=([^,\]]+)', tex_content))
        labels = standalone_labels | lstlisting_labels
        
        # Extract references (including \ref, \Cref, \cref)
        refs = set(re.findall(r'\\(?:[Cc]ref|ref)\{([^}]+)\}', tex_content))
        
        # Check for missing labels
        missing_labels = refs - labels
        if missing_labels:
            for label in missing_labels:
                self.errors.append(f"Reference '\\ref{{{label}}}' has no corresponding \\label")
                
        # Check for unused labels
        unused_labels = labels - refs
        if unused_labels:
            for label in unused_labels:
                self.warnings.append(f"Label '{label}' is defined but never referenced")
                
        self.info.append(f"Found {len(labels)} labels and {len(refs)} references")
        
        return len(missing_labels) == 0
        
    def validate_figures(self) -> bool:
        """Validate figure files and references."""
        print("\n🖼️  Validating figures...")
        
        tex_content = self.main_tex.read_text(encoding='utf-8')
        
        # Extract figure includes
        figure_includes = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex_content)
        
        missing_figures = []
        for fig_path in figure_includes:
            # Check multiple possible extensions and paths
            possible_paths = [
                self.paper_dir / fig_path,
                self.paper_dir / f"{fig_path}.png",
                self.paper_dir / f"{fig_path}.pdf",
                self.paper_dir / f"{fig_path}.jpg",
                self.paper_dir / "figs" / fig_path,
                self.paper_dir / "figures" / fig_path,
            ]
            
            if not any(p.exists() for p in possible_paths):
                missing_figures.append(fig_path)
                
        if missing_figures:
            for fig in missing_figures:
                self.errors.append(f"Figure file not found: {fig}")
                
        self.info.append(f"Found {len(figure_includes)} figure references")
        
        return len(missing_figures) == 0
        
    def validate_pdf_metadata(self) -> bool:
        """Validate PDF metadata if PDF exists."""
        print("\n📄 Validating PDF metadata...")
        
        if not self.main_pdf.exists():
            self.warnings.append("PDF file not found - skipping metadata validation")
            return True
            
        try:
            # Use pdfinfo to extract metadata
            result = subprocess.run(['pdfinfo', str(self.main_pdf)], 
                                  capture_output=True, text=True, check=True)
            metadata = result.stdout
            
            # Check for required metadata fields
            required_fields = ['Title:', 'Subject:', 'Author:']
            missing_fields = []
            
            for field in required_fields:
                if field not in metadata:
                    missing_fields.append(field.rstrip(':'))
                    
            if missing_fields:
                for field in missing_fields:
                    self.errors.append(f"PDF metadata missing: {field}")
                    
            # Extract and display metadata
            for line in metadata.split('\n'):
                if any(field in line for field in required_fields):
                    self.info.append(f"PDF metadata: {line.strip()}")
                    
            return len(missing_fields) == 0
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.warnings.append("Could not validate PDF metadata (pdfinfo not available)")
            return True
            
    def validate_compilation(self) -> bool:
        """Validate LaTeX compilation log."""
        print("\n⚙️  Validating compilation...")
        
        if not self.main_log.exists():
            self.warnings.append("Compilation log not found")
            return True
            
        log_content = self.main_log.read_text(encoding='utf-8', errors='ignore')
        
        # Check for errors
        error_patterns = [
            r'! .*',
            r'.*Error.*',
            r'.*Fatal.*',
        ]
        
        for pattern in error_patterns:
            errors = re.findall(pattern, log_content, re.IGNORECASE)
            for error in errors:
                if not any(skip in error.lower() for skip in ['font', 'warning']):
                    self.errors.append(f"Compilation error: {error.strip()}")
                    
        # Check for warnings
        warning_patterns = [
            r'Warning.*undefined.*reference',
            r'Warning.*Citation.*undefined',
            r'LaTeX Warning.*',
        ]
        
        for pattern in warning_patterns:
            warnings = re.findall(pattern, log_content)
            for warning in warnings[:5]:  # Limit to first 5 warnings
                self.warnings.append(f"Compilation warning: {warning.strip()}")
                
        # Check if PDF was generated successfully
        if "Output written on main.pdf" in log_content:
            self.info.append("PDF generated successfully")
        else:
            self.errors.append("PDF was not generated")
            
        return True
        
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
                
        if self.info:
            print(f"\n✅ INFO ({len(self.info)}):")
            for info in self.info:
                print(f"   • {info}")
                
        print(f"\n📊 RESULTS:")
        print(f"   • Errors: {len(self.errors)}")
        print(f"   • Warnings: {len(self.warnings)}")
        print(f"   • Status: {'❌ FAILED' if self.errors else '✅ PASSED'}")
        print("="*60)

def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate AlphaEvolve-ACGS paper')
    parser.add_argument('--dir', default='.', help='Paper directory (default: current)')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    
    args = parser.parse_args()
    
    validator = PaperValidator(args.dir)
    success = validator.validate_all()
    
    if args.strict and validator.warnings:
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
