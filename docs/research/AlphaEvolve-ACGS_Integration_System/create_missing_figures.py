#!/usr/bin/env python3
"""
Create missing figures for the AlphaEvolve-ACGS paper.
This script generates simple placeholder figures that are referenced in the document.
"""

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    from matplotlib.patches import FancyBboxPatch, Rectangle
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Matplotlib not available, creating text placeholders instead")

# Set style for professional academic figures
if HAS_MATPLOTLIB:
    plt.style.use('default')
    plt.rcParams['figure.facecolor'] = 'white'

def create_appeal_workflow():
    """Create the appeal workflow diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Define workflow steps
    steps = [
        "Policy Violation\nDetected",
        "Stakeholder\nAppeal Filed",
        "Evidence\nCollection",
        "Constitutional\nReview",
        "LLM-Assisted\nAnalysis",
        "Governance\nDecision",
        "Policy\nUpdate"
    ]

    # Position steps
    positions = [(1, 6), (3, 6), (5, 6), (7, 6), (5, 4), (3, 2), (1, 2)]

    # Draw boxes and arrows
    for i, (step, pos) in enumerate(zip(steps, positions)):
        # Create rounded rectangle
        box = FancyBboxPatch((pos[0]-0.4, pos[1]-0.3), 0.8, 0.6,
                           boxstyle="round,pad=0.1",
                           facecolor='lightblue',
                           edgecolor='navy',
                           linewidth=2)
        ax.add_patch(box)

        # Add text
        ax.text(pos[0], pos[1], step, ha='center', va='center',
                fontsize=10, fontweight='bold')

    # Draw arrows
    arrows = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,0)]
    for start, end in arrows:
        start_pos = positions[start]
        end_pos = positions[end]

        if start == 6 and end == 0:  # Feedback loop
            ax.annotate('', xy=(end_pos[0]-0.4, end_pos[1]),
                       xytext=(start_pos[0], start_pos[1]+0.3),
                       arrowprops=dict(arrowstyle='->', lw=2, color='red',
                                     connectionstyle="arc3,rad=0.3"))
        else:
            ax.annotate('', xy=(end_pos[0]-0.4, end_pos[1]),
                       xytext=(start_pos[0]+0.4, start_pos[1]),
                       arrowprops=dict(arrowstyle='->', lw=2, color='darkblue'))

    ax.set_xlim(0, 8)
    ax.set_ylim(1, 7)
    ax.set_title('Constitutional Appeal and Policy Update Workflow',
                fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('appeal_workflow.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_explainability_dashboard():
    """Create the explainability dashboard mockup."""
    fig = plt.figure(figsize=(14, 10))

    # Create grid layout
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('Constitutional Governance Explainability Dashboard',
                fontsize=18, fontweight='bold', y=0.95)

    # 1. Policy Decision Timeline
    ax1 = fig.add_subplot(gs[0, :])
    times = np.arange(10)
    decisions = np.random.choice(['ALLOW', 'DENY', 'WARN'], 10, p=[0.7, 0.2, 0.1])
    colors = {'ALLOW': 'green', 'DENY': 'red', 'WARN': 'orange'}

    for i, (time, decision) in enumerate(zip(times, decisions)):
        ax1.scatter(time, 0, c=colors[decision], s=100, alpha=0.7)
        ax1.text(time, 0.1, decision, ha='center', fontsize=8)

    ax1.set_xlim(-0.5, 9.5)
    ax1.set_ylim(-0.2, 0.3)
    ax1.set_xlabel('Time (Policy Evaluations)')
    ax1.set_title('Recent Policy Decisions', fontweight='bold')
    ax1.set_yticks([])

    # 2. Constitutional Principle Activation
    ax2 = fig.add_subplot(gs[1, 0])
    principles = ['Safety', 'Fairness', 'Privacy', 'Efficiency', 'Transparency']
    activation = [0.9, 0.7, 0.8, 0.6, 0.5]

    bars = ax2.barh(principles, activation, color='skyblue', alpha=0.7)
    ax2.set_xlim(0, 1)
    ax2.set_xlabel('Activation Level')
    ax2.set_title('Principle Activation', fontweight='bold')

    # 3. Rule Confidence Scores
    ax3 = fig.add_subplot(gs[1, 1])
    rules = ['Rule A', 'Rule B', 'Rule C', 'Rule D', 'Rule E']
    confidence = [0.95, 0.87, 0.92, 0.78, 0.83]

    ax3.bar(rules, confidence, color='lightcoral', alpha=0.7)
    ax3.set_ylim(0, 1)
    ax3.set_ylabel('Confidence Score')
    ax3.set_title('Rule Confidence', fontweight='bold')
    ax3.tick_params(axis='x', rotation=45)

    # 4. Violation Frequency
    ax4 = fig.add_subplot(gs[1, 2])
    violation_types = ['Type 1', 'Type 2', 'Type 3', 'Type 4']
    frequencies = [15, 8, 12, 5]

    ax4.pie(frequencies, labels=violation_types, autopct='%1.1f%%',
           colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
    ax4.set_title('Violation Distribution', fontweight='bold')

    # 5. System Performance Metrics
    ax5 = fig.add_subplot(gs[2, :])
    metrics = ['Latency (ms)', 'Throughput (req/s)', 'Accuracy (%)', 'Coverage (%)']
    values = [45, 1250, 94.2, 87.5]
    targets = [50, 1000, 95, 90]

    x = np.arange(len(metrics))
    width = 0.35

    ax5.bar(x - width/2, values, width, label='Current', color='steelblue', alpha=0.7)
    ax5.bar(x + width/2, targets, width, label='Target', color='orange', alpha=0.7)

    ax5.set_xlabel('Metrics')
    ax5.set_ylabel('Values')
    ax5.set_title('System Performance Overview', fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(metrics)
    ax5.legend()

    plt.tight_layout()
    plt.savefig('explainability_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_architecture_overview():
    """Create the main architecture overview figure."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Define layers
    layers = [
        {"name": "Constitutional Layer", "y": 8, "color": "#E8F4FD", "border": "#2E86AB"},
        {"name": "GS Engine (LLM-based Policy Synthesis)", "y": 6, "color": "#F8E8FF", "border": "#8E44AD"},
        {"name": "PGC (Real-time Enforcement)", "y": 4, "color": "#FFF8E8", "border": "#F39C12"},
        {"name": "Governed Evolutionary Layer", "y": 2, "color": "#E8FFE8", "border": "#27AE60"}
    ]

    # Draw layers
    for layer in layers:
        rect = Rectangle((1, layer["y"]-0.4), 12, 0.8,
                        facecolor=layer["color"],
                        edgecolor=layer["border"],
                        linewidth=2)
        ax.add_patch(rect)
        ax.text(7, layer["y"], layer["name"], ha='center', va='center',
               fontsize=12, fontweight='bold')

    # Add components within layers
    components = [
        # Constitutional Layer
        {"text": "Principles\n& Governance", "pos": (3, 8), "size": (1.5, 0.6)},
        {"text": "Stakeholder\nFeedback", "pos": (11, 8), "size": (1.5, 0.6)},

        # GS Engine
        {"text": "LLM\nSynthesis", "pos": (3, 6), "size": (1.5, 0.6)},
        {"text": "Validation\nPipeline", "pos": (7, 6), "size": (1.5, 0.6)},
        {"text": "Rule\nGeneration", "pos": (11, 6), "size": (1.5, 0.6)},

        # PGC
        {"text": "OPA\nEngine", "pos": (3, 4), "size": (1.5, 0.6)},
        {"text": "Decision\nCache", "pos": (7, 4), "size": (1.5, 0.6)},
        {"text": "Monitoring\n& Logging", "pos": (11, 4), "size": (1.5, 0.6)},

        # Evolutionary Layer
        {"text": "Population\nManagement", "pos": (3, 2), "size": (1.5, 0.6)},
        {"text": "Mutation\n& Selection", "pos": (7, 2), "size": (1.5, 0.6)},
        {"text": "Fitness\nEvaluation", "pos": (11, 2), "size": (1.5, 0.6)},
    ]

    for comp in components:
        rect = FancyBboxPatch((comp["pos"][0]-comp["size"][0]/2, comp["pos"][1]-comp["size"][1]/2),
                             comp["size"][0], comp["size"][1],
                             boxstyle="round,pad=0.05",
                             facecolor='white',
                             edgecolor='gray',
                             linewidth=1)
        ax.add_patch(rect)
        ax.text(comp["pos"][0], comp["pos"][1], comp["text"],
               ha='center', va='center', fontsize=9)

    # Add feedback arrows
    feedback_arrows = [
        ((11.5, 7.6), (11.5, 8.4)),  # Stakeholder feedback
        ((7, 5.6), (7, 6.4)),        # Validation feedback
        ((7, 3.6), (7, 4.4)),        # Monitoring feedback
        ((7, 1.6), (7, 2.4)),        # Evolution feedback
    ]

    for start, end in feedback_arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='<->', lw=2, color='red', alpha=0.7))

    ax.set_xlim(0, 14)
    ax.set_ylim(1, 9)
    ax.set_title('AlphaEvolve-ACGS Architecture Overview',
                fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('architecture_overview.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_text_placeholder(filename, description):
    """Create a simple text placeholder file."""
    with open(filename.replace('.png', '.txt'), 'w') as f:
        f.write(f"PLACEHOLDER: {description}\n")
        f.write("This is a placeholder for the missing figure.\n")
        f.write("The actual figure should be created with proper visualization tools.\n")

if __name__ == "__main__":
    print("Creating missing figures...")

    if HAS_MATPLOTLIB:
        try:
            create_appeal_workflow()
            print("✓ Created appeal_workflow.png")

            create_explainability_dashboard()
            print("✓ Created explainability_dashboard.png")

            create_architecture_overview()
            print("✓ Created architecture_overview.png")

            print("All figures created successfully!")
        except Exception as e:
            print(f"Error creating figures: {e}")
            print("Creating text placeholders instead...")
            create_text_placeholder("appeal_workflow.png", "Constitutional Appeal and Policy Update Workflow")
            create_text_placeholder("explainability_dashboard.png", "Constitutional Governance Explainability Dashboard")
            create_text_placeholder("architecture_overview.png", "AlphaEvolve-ACGS Architecture Overview")
    else:
        print("Creating text placeholders...")
        create_text_placeholder("appeal_workflow.png", "Constitutional Appeal and Policy Update Workflow")
        create_text_placeholder("explainability_dashboard.png", "Constitutional Governance Explainability Dashboard")
        create_text_placeholder("architecture_overview.png", "AlphaEvolve-ACGS Architecture Overview")
