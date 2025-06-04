#!/usr/bin/env python3
"""Debug script to check references and labels."""

import re

def debug_references():
    with open('main.tex', 'r', encoding='utf-8') as f:
        tex_content = f.read()
    
    # Extract labels (standalone and within environments like lstlisting)
    standalone_labels = set(re.findall(r'\\label\{([^}]+)\}', tex_content))
    # More flexible regex for lstlisting labels
    lstlisting_labels = set(re.findall(r'label=([^,\]]+)', tex_content))
    labels = standalone_labels | lstlisting_labels
    
    # Extract references (multiple patterns)
    refs1 = set(re.findall(r'\\ref\{([^}]+)\}', tex_content))
    refs2 = set(re.findall(r'\\Cref\{([^}]+)\}', tex_content))
    refs3 = set(re.findall(r'\\cref\{([^}]+)\}', tex_content))
    refs_combined = set(re.findall(r'\\(?:[Cc]ref|ref)\{([^}]+)\}', tex_content))
    
    print(f"Standalone labels found: {len(standalone_labels)}")
    print(f"Lstlisting labels found: {len(lstlisting_labels)}")
    print(f"Total labels found: {len(labels)}")
    print(f"\\ref found: {len(refs1)}")
    print(f"\\Cref found: {len(refs2)}")
    print(f"\\cref found: {len(refs3)}")
    print(f"Combined refs: {len(refs_combined)}")
    
    target_label = 'lst:appeal_workflow_dot_appendix'
    print(f"\nTarget label '{target_label}':")
    print(f"  In labels: {target_label in labels}")
    print(f"  In \\ref: {target_label in refs1}")
    print(f"  In \\Cref: {target_label in refs2}")
    print(f"  In \\cref: {target_label in refs3}")
    print(f"  In combined: {target_label in refs_combined}")
    
    # Check specific lines
    lines = tex_content.split('\n')
    for i, line in enumerate(lines, 1):
        if target_label in line:
            print(f"\nLine {i}: {line.strip()}")
    
    # Check missing references
    all_refs = refs1 | refs2 | refs3
    missing = all_refs - labels
    print(f"\nMissing labels: {missing}")

if __name__ == "__main__":
    debug_references()
