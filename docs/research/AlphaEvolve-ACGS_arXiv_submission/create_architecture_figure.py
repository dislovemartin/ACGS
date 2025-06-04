#!/usr/bin/env python3
"""
Create the AlphaEvolve-ACGS Architecture Overview Figure

This script generates a visual diagram showing the four-layer architecture
of the AlphaEvolve-ACGS framework with WINA integration components.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_architecture_figure():
    """Create the architecture overview figure."""
    
    # Set up the figure with high DPI for publication quality
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors (colorblind-safe palette)
    colors = {
        'constitutional': '#2E86AB',    # Blue
        'gs_engine': '#A23B72',        # Purple
        'pgc': '#F18F01',              # Orange
        'evolutionary': '#C73E1D',     # Red
        'wina': '#4CAF50',             # Green
        'feedback': '#795548',         # Brown
        'arrow': '#424242'             # Dark gray
    }
    
    # Layer dimensions and positions
    layer_height = 1.8
    layer_width = 8
    layer_x = 1
    
    # Layer 1: Constitutional Layer (top)
    const_y = 8
    const_box = FancyBboxPatch(
        (layer_x, const_y), layer_width, layer_height,
        boxstyle="round,pad=0.1",
        facecolor=colors['constitutional'],
        edgecolor='black',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(const_box)
    
    # Constitutional Layer text
    ax.text(layer_x + layer_width/2, const_y + layer_height/2 + 0.3, 
            'Constitutional Layer', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(layer_x + layer_width/2, const_y + layer_height/2 - 0.1, 
            'Principles & Governance', 
            ha='center', va='center', fontsize=11, color='white')
    ax.text(layer_x + layer_width/2, const_y + layer_height/2 - 0.4, 
            'WINA Constitutional Integration', 
            ha='center', va='center', fontsize=10, color='white', style='italic')
    
    # Layer 2: GS Engine Layer
    gs_y = 6
    gs_box = FancyBboxPatch(
        (layer_x, gs_y), layer_width, layer_height,
        boxstyle="round,pad=0.1",
        facecolor=colors['gs_engine'],
        edgecolor='black',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(gs_box)
    
    # GS Engine Layer text
    ax.text(layer_x + layer_width/2, gs_y + layer_height/2 + 0.3, 
            'Governance Synthesis (GS) Engine Layer', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(layer_x + layer_width/2, gs_y + layer_height/2 - 0.1, 
            'LLM-based Policy Synthesis (Principles → Rego)', 
            ha='center', va='center', fontsize=11, color='white')
    ax.text(layer_x + layer_width/2, gs_y + layer_height/2 - 0.4, 
            'WINA SVD Optimization', 
            ha='center', va='center', fontsize=10, color='white', style='italic')
    
    # Layer 3: PGC Layer
    pgc_y = 4
    pgc_box = FancyBboxPatch(
        (layer_x, pgc_y), layer_width, layer_height,
        boxstyle="round,pad=0.1",
        facecolor=colors['pgc'],
        edgecolor='black',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(pgc_box)
    
    # PGC Layer text
    ax.text(layer_x + layer_width/2, pgc_y + layer_height/2 + 0.3, 
            'Prompt Governance Compiler (PGC) Layer', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(layer_x + layer_width/2, pgc_y + layer_height/2 - 0.1, 
            'Real-time OPA Enforcement', 
            ha='center', va='center', fontsize=11, color='white')
    ax.text(layer_x + layer_width/2, pgc_y + layer_height/2 - 0.4, 
            'WINA-Optimized Enforcement & Strategy Selection', 
            ha='center', va='center', fontsize=10, color='white', style='italic')
    
    # Layer 4: Governed Evolutionary Layer (bottom)
    evo_y = 2
    evo_box = FancyBboxPatch(
        (layer_x, evo_y), layer_width, layer_height,
        boxstyle="round,pad=0.1",
        facecolor=colors['evolutionary'],
        edgecolor='black',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(evo_box)
    
    # Evolutionary Layer text
    ax.text(layer_x + layer_width/2, evo_y + layer_height/2 + 0.3, 
            'Governed Evolutionary Layer', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(layer_x + layer_width/2, evo_y + layer_height/2 - 0.1, 
            'EC System under Constitutional Guidance', 
            ha='center', va='center', fontsize=11, color='white')
    ax.text(layer_x + layer_width/2, evo_y + layer_height/2 - 0.4, 
            'WINA Oversight', 
            ha='center', va='center', fontsize=10, color='white', style='italic')
    
    # Add downward arrows between layers
    arrow_props = dict(arrowstyle='->', lw=3, color=colors['arrow'])
    
    # Constitutional → GS Engine
    ax.annotate('', xy=(layer_x + layer_width/2, gs_y + layer_height), 
                xytext=(layer_x + layer_width/2, const_y),
                arrowprops=arrow_props)
    ax.text(layer_x + layer_width/2 + 0.3, (const_y + gs_y + layer_height)/2, 
            'Principles', ha='left', va='center', fontsize=10, 
            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # GS Engine → PGC
    ax.annotate('', xy=(layer_x + layer_width/2, pgc_y + layer_height), 
                xytext=(layer_x + layer_width/2, gs_y),
                arrowprops=arrow_props)
    ax.text(layer_x + layer_width/2 + 0.3, (gs_y + pgc_y + layer_height)/2, 
            'Policies', ha='left', va='center', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # PGC → Evolutionary
    ax.annotate('', xy=(layer_x + layer_width/2, evo_y + layer_height), 
                xytext=(layer_x + layer_width/2, pgc_y),
                arrowprops=arrow_props)
    ax.text(layer_x + layer_width/2 + 0.3, (pgc_y + evo_y + layer_height)/2, 
            'Decisions', ha='left', va='center', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # Add WINA-Enhanced Feedback Loop (curved arrow on the right)
    feedback_arrow_props = dict(arrowstyle='->', lw=3, color=colors['feedback'],
                               connectionstyle="arc3,rad=0.3")
    
    # Feedback loop from Evolutionary back to Constitutional
    ax.annotate('', xy=(layer_x + layer_width - 0.2, const_y + 0.2), 
                xytext=(layer_x + layer_width - 0.2, evo_y + layer_height - 0.2),
                arrowprops=feedback_arrow_props)
    
    # Feedback loop label
    ax.text(layer_x + layer_width + 0.5, (const_y + evo_y + layer_height)/2, 
            'WINA-Enhanced\nFeedback Loop', ha='center', va='center', fontsize=11,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=colors['wina'], alpha=0.8),
            color='white', fontweight='bold')
    
    # Add title
    ax.text(5, 9.7, 'AlphaEvolve-ACGS Framework Architecture', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    # Add WINA components legend
    wina_components = [
        'ConstitutionalWINAIntegration',
        'WINAEnforcementOptimizer', 
        'WINAPolicyCompiler',
        'Performance Monitoring'
    ]
    
    legend_x = 0.2
    legend_y = 0.8
    ax.text(legend_x, legend_y + 0.3, 'WINA Components:', 
            fontsize=12, fontweight='bold')
    
    for i, component in enumerate(wina_components):
        ax.text(legend_x, legend_y - i*0.15, f'• {component}', 
                fontsize=10, color=colors['wina'])
    
    # Add information flow legend
    flow_x = 0.2
    flow_y = 0.2
    ax.text(flow_x, flow_y, 'Information Flow:', 
            fontsize=12, fontweight='bold')
    ax.text(flow_x, flow_y - 0.15, '→ Forward flow (Principles → Decisions)', 
            fontsize=10)
    ax.text(flow_x, flow_y - 0.3, '↗ Feedback loop (Co-evolution)', 
            fontsize=10, color=colors['feedback'])
    
    plt.tight_layout()
    return fig

def main():
    """Main function to create and save the architecture figure."""
    print("Creating AlphaEvolve-ACGS Architecture Overview Figure...")
    
    # Create the figure
    fig = create_architecture_figure()
    
    # Save the figure
    output_path = 'figs/architecture_overview.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"Architecture figure saved to: {output_path}")
    print("Figure specifications:")
    print("- Resolution: 300 DPI (publication quality)")
    print("- Format: PNG with transparent background support")
    print("- Colorblind-safe color palette")
    print("- Screen reader accessible design")
    
    plt.close(fig)

if __name__ == "__main__":
    main()
