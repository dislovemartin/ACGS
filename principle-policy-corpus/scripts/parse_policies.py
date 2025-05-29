#!/usr/bin/env python3
"""
Policy Parser and Normalizer

This script parses policy files from various sources and normalizes them into a consistent format.
"""

import json
import re
import os
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Generator, Any, Optional
from datetime import datetime

# Type aliases
PolicyEntry = Dict[str, Any]

class PolicyParser:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.counter = 0

    def generate_id(self, prefix: str = "P") -> str:
        """Generate a unique ID for each policy principle."""
        self.counter += 1
        return f"{prefix}-{self.counter:03d}"

    def parse_rego_file(self, filepath: Path) -> Tuple[str, str]:
        """Parse a Rego policy file and return (description, policy)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract comments (description)
        comments = "\n".join(re.findall(r'#.*', content))
        
        # Clean up the policy content
        policy = "\n".join(line for line in content.split('\n') 
                           if not line.strip().startswith('#'))
        
        return comments.strip(), policy.strip()

    def parse_json_policy(self, filepath: Path) -> Tuple[str, str]:
        """Parse a JSON policy file and return (description, policy_rule)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Handle different JSON policy formats
                description = ""
                policy_rule = {}
                
                # Azure Policy format
                if 'properties' in data:
                    description = data.get('properties', {}).get('description', '')
                    policy_rule = data.get('properties', {}).get('policyRule', {})
                # AWS IAM Policy format
                elif 'Statement' in data:
                    description = data.get('Description', '')
                    policy_rule = data
                # NIST OSCAL format
                elif 'controls' in data:
                    # This is a simplified version - would need expansion for full OSCAL support
                    description = data.get('metadata', {}).get('title', '')
                    policy_rule = data
                else:
                    description = ""
                    policy_rule = data
                
                return description, json.dumps(policy_rule, indent=2)
            except json.JSONDecodeError:
                return "", ""

    def parse_yaml_file(self, filepath: Path) -> Tuple[str, str]:
        """Parse a YAML policy file and return (description, policy)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                description = data.get('description', data.get('metadata', {}).get('description', ''))
                return str(description), yaml.dump(data, default_flow_style=False)
            except yaml.YAMLError:
                return "", ""

    def process_file(self, filepath: Path, source_repo: str) -> List[PolicyEntry]:
        """Process a single policy file and return a list of policy entries."""
        entries = []
        relative_path = str(filepath.relative_to(self.base_dir))
        
        try:
            if filepath.suffix == '.rego':
                description, policy = self.parse_rego_file(filepath)
                if policy:  # Only add if we have valid policy content
                    entries.append({
                        'principle_id': self.generate_id(),
                        'principle_text': description,
                        'policy_code': policy,
                        'source_repo': source_repo,
                        'source_path': relative_path,
                        'metadata': {
                            'domain': self.get_domain(source_repo),
                            'framework': 'Rego',
                            'date_collected': datetime.now().strftime('%Y-%m-%d')
                        },
                        'alignment_notes': ''
                    })
            
            elif filepath.suffix == '.json':
                description, policy = self.parse_json_policy(filepath)
                if policy:  # Only add if we have valid policy content
                    entries.append({
                        'principle_id': self.generate_id(),
                        'principle_text': description,
                        'policy_code': policy,
                        'source_repo': source_repo,
                        'source_path': relative_path,
                        'metadata': {
                            'domain': self.get_domain(source_repo),
                            'framework': 'JSON',
                            'date_collected': datetime.now().strftime('%Y-%m-%d')
                        },
                        'alignment_notes': ''
                    })
            
            elif filepath.suffix in ['.yaml', '.yml']:
                description, policy = self.parse_yaml_file(filepath)
                if policy:  # Only add if we have valid policy content
                    entries.append({
                        'principle_id': self.generate_id(),
                        'principle_text': description,
                        'policy_code': policy,
                        'source_repo': source_repo,
                        'source_path': relative_path,
                        'metadata': {
                            'domain': self.get_domain(source_repo),
                            'framework': 'YAML',
                            'date_collected': datetime.now().strftime('%Y-%m-%d')
                        },
                        'alignment_notes': ''
                    })
        
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
        
        return entries

    def get_domain(self, source_repo: str) -> str:
        """Determine the domain based on the source repository name."""
        repo_lower = source_repo.lower()
        if 'azure' in repo_lower:
            return 'Azure'
        elif 'aws' in repo_lower or 'iam' in repo_lower:
            return 'AWS'
        elif 'nist' in repo_lower or 'oscal' in repo_lower:
            return 'NIST'
        elif 'gatekeeper' in repo_lower:
            return 'Kubernetes'
        else:
            return 'Generic'

    def find_policy_files(self, directory: Path) -> List[Path]:
        """Recursively find all policy files in a directory."""
        policy_files = []
        for ext in ['*.rego', '*.json', '*.yaml', '*.yml']:
            policy_files.extend(directory.rglob(ext))
        return policy_files

    def process_directory(self, directory: str, source_name: str) -> List[PolicyEntry]:
        """Process all policy files in a directory."""
        dir_path = self.base_dir / directory
        if not dir_path.exists():
            print(f"Directory not found: {dir_path}")
            return []
        
        policy_files = self.find_policy_files(dir_path)
        print(f"Found {len(policy_files)} policy files in {directory}")
        
        all_entries = []
        for filepath in policy_files:
            entries = self.process_file(filepath, source_name)
            all_entries.extend(entries)
        
        return all_entries

    def save_entries(self, entries: List[PolicyEntry], filename: str) -> None:
        """Save entries to a JSONL file."""
        output_file = self.output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"Saved {len(entries)} entries to {output_file}")

def main():
    base_dir = Path(__file__).parent.parent
    parser = PolicyParser(base_dir)
    
    # Process each source directory
    sources = [
        ('opa-library', 'OPA Library'),
        ('gatekeeper-library', 'Gatekeeper Library'),
        ('azure-policy', 'Azure Policy'),
        ('Community-Policy', 'Azure Community Policy'),
        ('aws-iam-examples', 'AWS IAM Examples'),
        ('nist-oscal-profiles', 'NIST OSCAL Profiles')
    ]
    
    all_entries = []
    for dir_name, source_name in sources:
        print(f"\nProcessing {source_name}...")
        entries = parser.process_directory(dir_name, source_name)
        all_entries.extend(entries)
        
        # Save entries for each source
        if entries:
            output_file = f"{source_name.lower().replace(' ', '_')}_policies.jsonl"
            parser.save_entries(entries, output_file)
    
    # Save all entries to a single file
    if all_entries:
        parser.save_entries(all_entries, "all_policies.jsonl")
    
    print(f"\nProcessing complete. Processed {len(all_entries)} policy entries in total.")

if __name__ == "__main__":
    main()
