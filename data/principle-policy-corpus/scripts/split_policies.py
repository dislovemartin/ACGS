#!/usr/bin/env python3
"""
Policy Corpus Splitter

This script splits the all_policies.jsonl file into multiple smaller files.
"""

import json
import os
import math
from pathlib import Path
from typing import List, Dict, Any

def split_policies(input_file: str, num_parts: int = 10) -> None:
    """
    Split the input JSONL file into multiple smaller files.
    
    Args:
        input_file: Path to the input JSONL file
        num_parts: Number of parts to split the file into
    """
    # Read all lines from the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    print(f"Read {total_lines} policies from {input_file}")
    
    # Calculate lines per part
    lines_per_part = math.ceil(total_lines / num_parts)
    print(f"Splitting into {num_parts} parts, approximately {lines_per_part} policies per part")
    
    # Create output directory if it doesn't exist
    output_dir = Path(input_file).parent / 'split_policies'
    output_dir.mkdir(exist_ok=True)
    
    # Split and write to files
    for i in range(num_parts):
        start_idx = i * lines_per_part
        end_idx = min((i + 1) * lines_per_part, total_lines)
        
        if start_idx >= total_lines:
            break
            
        part_lines = lines[start_idx:end_idx]
        output_file = output_dir / f'policies_part_{i+1:02d}_of_{num_parts}.jsonl'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(part_lines)
        
        print(f"Created {output_file} with {len(part_lines)} policies")

def main():
    # Configuration
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'output' / 'all_policies.jsonl'
    num_parts = 10
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return
    
    print(f"Splitting {input_file} into {num_parts} parts...")
    split_policies(str(input_file), num_parts)
    print("\nSplitting complete!")
    
    # Print summary
    output_dir = input_file.parent / 'split_policies'
    if output_dir.exists():
        print("\nGenerated files:")
        for f in sorted(output_dir.glob('*.jsonl')):
            num_lines = sum(1 for _ in open(f, 'r', encoding='utf-8'))
            print(f"- {f.name}: {num_lines} policies")

if __name__ == "__main__":
    main()
