#!/usr/bin/env python3
"""
Publication Compliance Assessment for AlphaEvolve-ACGS Integration System
Validates compliance with ACM FAccT 2025 submission requirements
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

class PublicationComplianceAssessment:
    def __init__(self, paper_path: str = "main.tex"):
        self.paper_path = Path(paper_path)
        self.pdf_path = Path("main.pdf")
        self.compliance_report = {
            "formatting": {},
            "content": {},
            "submission": {},
            "ethics": {},
            "overall_score": 0
        }
    
    def assess_formatting_compliance(self) -> Dict:
        """Assess ACM FAccT 2025 formatting requirements"""
        print("🔍 Assessing formatting compliance...")
        
        tex_content = self.paper_path.read_text(encoding='utf-8')
        formatting_results = {}
        
        # Check document class and options
        acmart_pattern = r'\\documentclass\[([^\]]*)\]\{acmart\}'
        acmart_match = re.search(acmart_pattern, tex_content)
        
        if acmart_match:
            options = acmart_match.group(1)
            formatting_results["document_class"] = {
                "status": "✅ PASS",
                "details": f"Uses acmart class with options: {options}",
                "compliant": "manuscript" in options and "review" in options
            }
        else:
            formatting_results["document_class"] = {
                "status": "❌ FAIL",
                "details": "Does not use ACM acmart document class",
                "compliant": False
            }
        
        # Check page length (14 pages max + 1 endmatter + unlimited references)
        if self.pdf_path.exists():
            try:
                result = subprocess.run(['pdfinfo', str(self.pdf_path)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    pages_match = re.search(r'Pages:\s+(\d+)', result.stdout)
                    if pages_match:
                        page_count = int(pages_match.group(1))
                        formatting_results["page_length"] = {
                            "status": "✅ PASS" if page_count <= 15 else "⚠️ WARNING",
                            "details": f"Document has {page_count} pages (limit: 14 + 1 endmatter + unlimited refs)",
                            "compliant": page_count <= 25  # Reasonable upper bound
                        }
            except Exception as e:
                formatting_results["page_length"] = {
                    "status": "⚠️ UNKNOWN",
                    "details": f"Could not determine page count: {e}",
                    "compliant": None
                }
        
        # Check anonymization for review
        author_patterns = [
            r'\\author\{[^}]+\}',
            r'\\affiliation\{[^}]+\}',
            r'\\email\{[^}]+\}'
        ]
        
        has_author_info = any(re.search(pattern, tex_content) for pattern in author_patterns)
        formatting_results["anonymization"] = {
            "status": "⚠️ WARNING" if has_author_info else "✅ PASS",
            "details": "Author information found - ensure anonymous=true for submission" if has_author_info else "No author information found",
            "compliant": not has_author_info
        }
        
        # Check reference format
        ref_patterns = [
            r'\\bibliographystyle\{ACM-Reference-Format\}',
            r'\\bibliography\{[^}]+\}'
        ]
        
        has_acm_refs = any(re.search(pattern, tex_content) for pattern in ref_patterns)
        formatting_results["references"] = {
            "status": "✅ PASS" if has_acm_refs else "⚠️ WARNING",
            "details": "Uses ACM reference format" if has_acm_refs else "Reference format needs verification",
            "compliant": has_acm_refs
        }
        
        return formatting_results
    
    def assess_content_compliance(self) -> Dict:
        """Assess content requirements for ACM FAccT 2025"""
        print("📝 Assessing content compliance...")
        
        tex_content = self.paper_path.read_text(encoding='utf-8')
        content_results = {}
        
        # Check for required sections
        required_sections = [
            (r'\\section\{.*[Ii]ntroduction.*\}', "Introduction"),
            (r'\\section\{.*[Rr]elated [Ww]ork.*\}', "Related Work"),
            (r'\\section\{.*[Mm]ethod.*\}|\\section\{.*[Aa]pproach.*\}', "Methodology"),
            (r'\\section\{.*[Rr]esults.*\}|\\section\{.*[Ee]valuation.*\}', "Results/Evaluation"),
            (r'\\section\{.*[Cc]onclusion.*\}', "Conclusion")
        ]
        
        section_compliance = {}
        for pattern, section_name in required_sections:
            found = bool(re.search(pattern, tex_content, re.IGNORECASE))
            section_compliance[section_name] = {
                "status": "✅ PASS" if found else "⚠️ WARNING",
                "details": f"{section_name} section {'found' if found else 'not found'}",
                "compliant": found
            }
        
        content_results["sections"] = section_compliance
        
        # Check for ethical considerations
        ethics_patterns = [
            r'[Ee]thical?\s+[Cc]onsiderations?',
            r'[Ee]thics?\s+[Ss]tatement',
            r'[Aa]dverse\s+[Ii]mpact',
            r'[Hh]uman\s+[Ss]ubjects?'
        ]
        
        has_ethics = any(re.search(pattern, tex_content) for pattern in ethics_patterns)
        content_results["ethics"] = {
            "status": "✅ PASS" if has_ethics else "⚠️ WARNING",
            "details": "Ethical considerations addressed" if has_ethics else "Consider adding ethical considerations section",
            "compliant": has_ethics
        }
        
        # Check abstract length (should be ≤250 words)
        abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex_content, re.DOTALL)
        if abstract_match:
            abstract_text = abstract_match.group(1)
            word_count = len(abstract_text.split())
            content_results["abstract"] = {
                "status": "✅ PASS" if word_count <= 250 else "⚠️ WARNING",
                "details": f"Abstract has {word_count} words (limit: 250)",
                "compliant": word_count <= 250
            }
        else:
            content_results["abstract"] = {
                "status": "❌ FAIL",
                "details": "No abstract found",
                "compliant": False
            }
        
        return content_results
    
    def assess_submission_readiness(self) -> Dict:
        """Assess submission package readiness"""
        print("📦 Assessing submission readiness...")
        
        submission_results = {}
        
        # Check required files
        required_files = [
            ("main.tex", "Main LaTeX source"),
            ("main.pdf", "Compiled PDF"),
            ("main.bib", "Bibliography file")
        ]
        
        file_compliance = {}
        for filename, description in required_files:
            exists = Path(filename).exists()
            file_compliance[filename] = {
                "status": "✅ PASS" if exists else "❌ FAIL",
                "details": f"{description} {'exists' if exists else 'missing'}",
                "compliant": exists
            }
        
        submission_results["files"] = file_compliance
        
        # Check PDF properties
        if Path("main.pdf").exists():
            try:
                result = subprocess.run(['pdfinfo', 'main.pdf'], capture_output=True, text=True)
                if result.returncode == 0:
                    pdf_info = result.stdout
                    has_title = "Title:" in pdf_info and "AlphaEvolve-ACGS" in pdf_info
                    has_author = "Author:" in pdf_info
                    
                    submission_results["pdf_metadata"] = {
                        "status": "✅ PASS" if has_title else "⚠️ WARNING",
                        "details": f"PDF metadata: Title {'present' if has_title else 'missing'}, Author {'present' if has_author else 'missing'}",
                        "compliant": has_title
                    }
            except Exception as e:
                submission_results["pdf_metadata"] = {
                    "status": "⚠️ UNKNOWN",
                    "details": f"Could not check PDF metadata: {e}",
                    "compliant": None
                }
        
        return submission_results
    
    def generate_compliance_report(self) -> str:
        """Generate comprehensive compliance report"""
        print("📋 Generating compliance report...")
        
        # Run all assessments
        self.compliance_report["formatting"] = self.assess_formatting_compliance()
        self.compliance_report["content"] = self.assess_content_compliance()
        self.compliance_report["submission"] = self.assess_submission_readiness()
        
        # Calculate overall compliance score
        total_checks = 0
        passed_checks = 0
        
        for category in ["formatting", "content", "submission"]:
            for check_name, check_result in self.compliance_report[category].items():
                if isinstance(check_result, dict) and "compliant" in check_result:
                    total_checks += 1
                    if check_result["compliant"]:
                        passed_checks += 1
                elif isinstance(check_result, dict):
                    # Handle nested results (like sections)
                    for subcheck_name, subcheck_result in check_result.items():
                        if isinstance(subcheck_result, dict) and "compliant" in subcheck_result:
                            total_checks += 1
                            if subcheck_result["compliant"]:
                                passed_checks += 1
        
        self.compliance_report["overall_score"] = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Generate report
        report = self._format_compliance_report()
        return report
    
    def _format_compliance_report(self) -> str:
        """Format the compliance report for display"""
        report_lines = [
            "# ACM FAccT 2025 Publication Compliance Assessment",
            f"**Assessment Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Overall Compliance Score:** {self.compliance_report['overall_score']:.1f}%",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add summary based on score
        score = self.compliance_report["overall_score"]
        if score >= 90:
            report_lines.append("✅ **EXCELLENT** - Paper is ready for submission with minor adjustments")
        elif score >= 80:
            report_lines.append("✅ **GOOD** - Paper is nearly ready with some improvements needed")
        elif score >= 70:
            report_lines.append("⚠️ **ACCEPTABLE** - Paper needs moderate improvements before submission")
        else:
            report_lines.append("❌ **NEEDS WORK** - Significant improvements required before submission")
        
        report_lines.extend([
            "",
            "## Detailed Assessment Results",
            ""
        ])
        
        # Add detailed results for each category
        for category_name, category_results in self.compliance_report.items():
            if category_name == "overall_score":
                continue
                
            report_lines.append(f"### {category_name.title()} Compliance")
            report_lines.append("")
            
            for check_name, check_result in category_results.items():
                if isinstance(check_result, dict) and "status" in check_result:
                    report_lines.append(f"- **{check_name}**: {check_result['status']}")
                    report_lines.append(f"  - {check_result['details']}")
                elif isinstance(check_result, dict):
                    # Handle nested results
                    report_lines.append(f"- **{check_name}**:")
                    for subcheck_name, subcheck_result in check_result.items():
                        if isinstance(subcheck_result, dict) and "status" in subcheck_result:
                            report_lines.append(f"  - {subcheck_name}: {subcheck_result['status']}")
                            report_lines.append(f"    - {subcheck_result['details']}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)

def main():
    """Run publication compliance assessment"""
    assessor = PublicationComplianceAssessment()
    report = assessor.generate_compliance_report()
    
    # Save report
    report_path = Path("publication_compliance_report.md")
    report_path.write_text(report, encoding='utf-8')
    
    print(f"✅ Compliance assessment complete!")
    print(f"📄 Report saved to: {report_path}")
    print(f"📊 Overall compliance score: {assessor.compliance_report['overall_score']:.1f}%")
    
    return report

if __name__ == "__main__":
    main()
