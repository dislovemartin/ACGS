#!/usr/bin/env python3
"""
Seed MAB Prompt Templates

Seeds the database with the 4 default prompt templates for Multi-Armed Bandit optimization:
1. Constitutional - For constitutional compliance and governance
2. Safety Critical - For safety-critical applications
3. Fairness Aware - For bias mitigation and fairness
4. Adaptive - For general-purpose adaptive prompting

Usage:
    python scripts/seed_mab_prompt_templates.py
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timezone
import hashlib
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://acgs_user:acgs_password@localhost:5434/acgs_pgp_db')

# Default prompt templates for MAB optimization
DEFAULT_TEMPLATES = [
    {
        'template_id': 'constitutional_v1_0',
        'name': 'Constitutional Compliance Template',
        'template_content': '''You are an AI assistant specialized in constitutional governance and policy synthesis. 

Your task is to generate policies that strictly adhere to constitutional principles while ensuring democratic legitimacy and rule of law.

Context: {context}
Principles: {principles}
Target Format: {target_format}

Requirements:
1. Ensure constitutional compliance with all provided principles
2. Maintain democratic legitimacy and transparency
3. Consider stakeholder impact and public interest
4. Generate clear, enforceable policy language
5. Include rationale for constitutional alignment

Generate a {target_format} policy that embodies these constitutional principles:''',
        'category': 'constitutional',
        'version': '1.0',
        'metadata_json': {
            'description': 'Template optimized for constitutional compliance and democratic governance',
            'use_cases': ['constitutional_synthesis', 'governance_policies', 'democratic_legitimacy'],
            'optimization_focus': 'constitutional_compliance',
            'expected_performance': {
                'constitutional_compliance': 0.95,
                'policy_quality': 0.85,
                'semantic_similarity': 0.80,
                'bias_mitigation': 0.75
            }
        }
    },
    {
        'template_id': 'safety_critical_v1_0',
        'name': 'Safety-Critical Applications Template',
        'template_content': '''You are an AI assistant specialized in safety-critical policy generation with the highest standards of reliability and risk mitigation.

Your task is to generate policies for safety-critical applications where failure could result in harm to individuals or systems.

Context: {context}
Principles: {principles}
Target Format: {target_format}
Safety Level: {safety_level}

Critical Requirements:
1. Prioritize safety above all other considerations
2. Implement fail-safe mechanisms and redundancy
3. Ensure comprehensive risk assessment coverage
4. Generate conservative, well-tested policy logic
5. Include explicit safety validation criteria
6. Consider worst-case scenarios and edge cases

Generate a {target_format} policy with maximum safety assurance:''',
        'category': 'safety_critical',
        'version': '1.0',
        'metadata_json': {
            'description': 'Template optimized for safety-critical applications with maximum reliability',
            'use_cases': ['safety_critical_systems', 'high_risk_policies', 'fail_safe_mechanisms'],
            'optimization_focus': 'safety_assurance',
            'expected_performance': {
                'constitutional_compliance': 0.90,
                'policy_quality': 0.95,
                'semantic_similarity': 0.85,
                'bias_mitigation': 0.80
            }
        }
    },
    {
        'template_id': 'fairness_aware_v1_0',
        'name': 'Fairness and Bias Mitigation Template',
        'template_content': '''You are an AI assistant specialized in generating fair, unbiased policies that promote equity and inclusion across all demographic groups.

Your task is to generate policies that actively mitigate bias and promote fairness while maintaining effectiveness and constitutional compliance.

Context: {context}
Principles: {principles}
Target Format: {target_format}
Protected Attributes: {protected_attributes}

Fairness Requirements:
1. Actively identify and mitigate potential biases
2. Ensure equitable treatment across all demographic groups
3. Consider intersectionality and compound disadvantages
4. Implement fairness metrics and monitoring
5. Promote inclusive language and accessibility
6. Balance individual fairness with group fairness

Generate a {target_format} policy that maximizes fairness and minimizes bias:''',
        'category': 'fairness_aware',
        'version': '1.0',
        'metadata_json': {
            'description': 'Template optimized for bias mitigation and fairness across demographic groups',
            'use_cases': ['bias_mitigation', 'fairness_optimization', 'inclusive_policies'],
            'optimization_focus': 'bias_mitigation',
            'expected_performance': {
                'constitutional_compliance': 0.85,
                'policy_quality': 0.80,
                'semantic_similarity': 0.75,
                'bias_mitigation': 0.95
            }
        }
    },
    {
        'template_id': 'adaptive_general_v1_0',
        'name': 'Adaptive General-Purpose Template',
        'template_content': '''You are an AI assistant capable of adapting your policy generation approach based on the specific context and requirements provided.

Your task is to generate high-quality policies that balance multiple objectives while adapting to the specific domain and constraints.

Context: {context}
Principles: {principles}
Target Format: {target_format}
Domain: {domain}
Complexity Level: {complexity_level}

Adaptive Requirements:
1. Analyze the context to determine optimal approach
2. Balance competing objectives based on domain requirements
3. Adapt language and structure to target audience
4. Incorporate domain-specific best practices
5. Optimize for the most critical success metrics
6. Maintain flexibility while ensuring consistency

Generate a {target_format} policy optimized for this specific context:''',
        'category': 'adaptive',
        'version': '1.0',
        'metadata_json': {
            'description': 'Template that adapts to different contexts and balances multiple objectives',
            'use_cases': ['general_purpose', 'multi_objective_optimization', 'context_adaptation'],
            'optimization_focus': 'balanced_performance',
            'expected_performance': {
                'constitutional_compliance': 0.85,
                'policy_quality': 0.85,
                'semantic_similarity': 0.85,
                'bias_mitigation': 0.80
            }
        }
    }
]


async def seed_prompt_templates():
    """Seed the database with default MAB prompt templates."""
    
    # Parse the database URL to extract connection parameters
    if DATABASE_URL.startswith('postgresql+asyncpg://'):
        db_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    else:
        db_url = DATABASE_URL.replace('postgresql://', 'postgresql://')
    
    print(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
    
    try:
        # Connect to the database
        conn = await asyncpg.connect(db_url)
        print("✅ Database connection successful")
        
        # Check if templates already exist
        existing_count = await conn.fetchval(
            "SELECT COUNT(*) FROM prompt_templates"
        )
        
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing prompt templates")
            response = input("Do you want to clear existing templates and reseed? (y/N): ")
            if response.lower() != 'y':
                print("❌ Seeding cancelled")
                await conn.close()
                return
            
            # Clear existing templates
            await conn.execute("DELETE FROM prompt_templates")
            print("🗑️  Cleared existing prompt templates")
        
        # Insert default templates
        inserted_count = 0
        for template in DEFAULT_TEMPLATES:
            try:
                await conn.execute("""
                    INSERT INTO prompt_templates (
                        template_id, name, template_content, category, version,
                        metadata_json, created_at, updated_at, total_uses,
                        total_rewards, success_count, average_reward,
                        confidence_lower, confidence_upper, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """, 
                    template['template_id'],
                    template['name'],
                    template['template_content'],
                    template['category'],
                    template['version'],
                    json.dumps(template['metadata_json']),
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    0,  # total_uses
                    0.0,  # total_rewards
                    0,  # success_count
                    0.0,  # average_reward
                    0.0,  # confidence_lower
                    1.0,  # confidence_upper
                    True  # is_active
                )
                
                inserted_count += 1
                print(f"✅ Inserted template: {template['name']} ({template['template_id']})")
                
            except Exception as e:
                print(f"❌ Failed to insert template {template['template_id']}: {e}")
        
        print(f"\n🎉 Successfully seeded {inserted_count}/{len(DEFAULT_TEMPLATES)} prompt templates")
        
        # Verify the insertion
        final_count = await conn.fetchval("SELECT COUNT(*) FROM prompt_templates")
        print(f"📊 Total prompt templates in database: {final_count}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting MAB Prompt Template Seeding...")
    success = asyncio.run(seed_prompt_templates())
    
    if success:
        print("\n✅ MAB prompt template seeding completed successfully!")
        print("\nNext steps:")
        print("1. Start the GS service to test MAB integration")
        print("2. Test MAB API endpoints: /api/v1/mab/status, /api/v1/mab/metrics")
        print("3. Run constitutional synthesis with MAB optimization")
    else:
        print("\n❌ MAB prompt template seeding failed!")
        sys.exit(1)
