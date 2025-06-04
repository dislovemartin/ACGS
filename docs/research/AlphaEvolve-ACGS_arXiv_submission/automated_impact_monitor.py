#!/usr/bin/env python3
"""
Automated Impact Monitoring Script for AlphaEvolve-ACGS arXiv Preprint
Tracks various metrics and generates reports for community engagement assessment.
"""

import requests
import json
import csv
import datetime
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('impact_monitoring.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class MetricEntry:
    """Data class for tracking metrics"""
    date: str
    metric_type: str
    platform: str
    metric_name: str
    value: int
    notes: str
    source_url: str = ""

class ImpactMonitor:
    """Main class for monitoring paper impact across various platforms"""
    
    def __init__(self, arxiv_id: str = "", paper_title: str = ""):
        self.arxiv_id = arxiv_id
        self.paper_title = paper_title
        self.metrics_file = "impact_tracking_data.csv"
        self.report_file = "impact_report.md"
        
        # Initialize CSV file if it doesn't exist
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.metrics_file):
            headers = ["Date", "Metric_Type", "Platform", "Metric_Name", 
                      "Value", "Notes", "Source_URL"]
            with open(self.metrics_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def add_metric(self, metric: MetricEntry):
        """Add a metric entry to the CSV file"""
        with open(self.metrics_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                metric.date, metric.metric_type, metric.platform,
                metric.metric_name, metric.value, metric.notes, metric.source_url
            ])
    
    def check_arxiv_stats(self) -> Optional[MetricEntry]:
        """Check arXiv download statistics (manual entry required)"""
        # Note: arXiv doesn't provide public API for download stats
        # This would need to be manually updated from arXiv admin interface
        logging.info("arXiv stats check - manual update required")
        return None
    
    def check_google_scholar_citations(self) -> Optional[MetricEntry]:
        """Check Google Scholar citations (requires manual verification)"""
        # Note: Google Scholar doesn't have official API
        # This would need manual checking or use of unofficial scrapers
        logging.info("Google Scholar check - manual verification required")
        return None
    
    def check_semantic_scholar_citations(self) -> Optional[MetricEntry]:
        """Check Semantic Scholar citations using their API"""
        if not self.paper_title:
            logging.warning("Paper title not set for Semantic Scholar search")
            return None
        
        try:
            # Semantic Scholar API endpoint
            url = f"https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": self.paper_title,
                "limit": 1,
                "fields": "citationCount,title,authors"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    paper = data['data'][0]
                    citation_count = paper.get('citationCount', 0)
                    
                    metric = MetricEntry(
                        date=datetime.date.today().isoformat(),
                        metric_type="Citations",
                        platform="Semantic_Scholar",
                        metric_name="Citation_Count",
                        value=citation_count,
                        notes="Automated check",
                        source_url="https://www.semanticscholar.org/"
                    )
                    return metric
        except Exception as e:
            logging.error(f"Error checking Semantic Scholar: {e}")
        
        return None
    
    def manual_metric_entry(self, metric_type: str, platform: str, 
                           metric_name: str, value: int, notes: str = ""):
        """Manually add a metric entry"""
        metric = MetricEntry(
            date=datetime.date.today().isoformat(),
            metric_type=metric_type,
            platform=platform,
            metric_name=metric_name,
            value=value,
            notes=notes
        )
        self.add_metric(metric)
        logging.info(f"Added manual metric: {metric_type}/{platform}/{metric_name} = {value}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive impact report"""
        if not os.path.exists(self.metrics_file):
            return "No metrics data available"
        
        # Read all metrics
        metrics = []
        with open(self.metrics_file, 'r') as f:
            reader = csv.DictReader(f)
            metrics = list(reader)
        
        if not metrics:
            return "No metrics data available"
        
        # Generate report
        report_date = datetime.date.today().isoformat()
        report = f"""# AlphaEvolve-ACGS Impact Report
Generated: {report_date}

## Summary Statistics

"""
        
        # Group metrics by type
        metric_types = {}
        for metric in metrics:
            mtype = metric['Metric_Type']
            if mtype not in metric_types:
                metric_types[mtype] = []
            metric_types[mtype].append(metric)
        
        # Generate sections for each metric type
        for mtype, mlist in metric_types.items():
            report += f"### {mtype}\n\n"
            
            # Get latest values for each platform/metric combination
            latest_values = {}
            for m in mlist:
                key = f"{m['Platform']}/{m['Metric_Name']}"
                if key not in latest_values or m['Date'] > latest_values[key]['Date']:
                    latest_values[key] = m
            
            for key, m in latest_values.items():
                report += f"- **{m['Platform']} {m['Metric_Name']}**: {m['Value']} (as of {m['Date']})\n"
            
            report += "\n"
        
        # Add trend analysis if we have multiple data points
        report += "## Trends\n\n"
        report += "*Trend analysis would be added here based on historical data*\n\n"
        
        # Add recommendations
        report += "## Recommendations\n\n"
        report += "Based on current metrics:\n"
        report += "- Continue social media engagement\n"
        report += "- Follow up on collaboration inquiries\n"
        report += "- Monitor citation development\n"
        report += "- Expand outreach to underperforming channels\n\n"
        
        # Save report
        with open(self.report_file, 'w') as f:
            f.write(report)
        
        return report
    
    def run_daily_check(self):
        """Run daily automated checks"""
        logging.info("Starting daily impact monitoring check")
        
        # Check Semantic Scholar citations
        semantic_metric = self.check_semantic_scholar_citations()
        if semantic_metric:
            self.add_metric(semantic_metric)
        
        # Generate updated report
        self.generate_report()
        
        logging.info("Daily check completed")

def main():
    """Main function for running the impact monitor"""
    # Initialize monitor
    monitor = ImpactMonitor(
        arxiv_id="",  # To be filled after arXiv submission
        paper_title="AlphaEvolve-ACGS: A Co-Evolutionary Framework for LLM-Driven Constitutional Governance in Evolutionary Computation"
    )
    
    # Example usage - add manual metrics
    print("AlphaEvolve-ACGS Impact Monitor")
    print("==============================")
    print()
    print("Options:")
    print("1. Add manual metric")
    print("2. Run daily check")
    print("3. Generate report")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Manual metric entry
            metric_type = input("Metric type (Downloads/Social_Media/Citations/etc.): ")
            platform = input("Platform (arXiv/LinkedIn/Twitter/etc.): ")
            metric_name = input("Metric name: ")
            value = int(input("Value: "))
            notes = input("Notes (optional): ")
            
            monitor.manual_metric_entry(metric_type, platform, metric_name, value, notes)
            print("Metric added successfully!")
        
        elif choice == "2":
            monitor.run_daily_check()
            print("Daily check completed!")
        
        elif choice == "3":
            report = monitor.generate_report()
            print("Report generated!")
            print("\nReport preview:")
            print("=" * 50)
            print(report[:500] + "..." if len(report) > 500 else report)
        
        elif choice == "4":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
