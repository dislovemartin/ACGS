#!/usr/bin/env python3
"""
Debug MAB Template Selection

Debug the template selection issue in the MAB system.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://acgs_user:acgs_password@localhost:5434/acgs_pgp_db'
os.environ['PYTHONPATH'] = '/home/dislove/ACGS-master/src/backend:/home/dislove/ACGS-master/src/backend/shared'


async def debug_template_selection():
    """Debug template selection logic."""
    print("🔍 Debugging MAB Template Selection...")
    
    try:
        from gs_service.app.core.mab_integration import MABIntegratedGSService
        
        # Initialize MAB service
        mab_service = MABIntegratedGSService()
        print("✅ MAB service initialized")
        
        # Check registered templates
        print(f"\n📋 Registered Templates ({len(mab_service.mab_optimizer.prompt_templates)}):")
        for template_id, template in mab_service.mab_optimizer.prompt_templates.items():
            print(f"   - {template_id}: {template.name} (category: {template.category})")
        
        # Check MAB algorithm arms
        print(f"\n🎯 MAB Algorithm Arms:")
        if hasattr(mab_service.mab_optimizer.mab_algorithm, 'alpha'):
            print("   Thompson Sampling arms:")
            for arm_id in mab_service.mab_optimizer.mab_algorithm.alpha.keys():
                alpha = mab_service.mab_optimizer.mab_algorithm.alpha[arm_id]
                beta = mab_service.mab_optimizer.mab_algorithm.beta[arm_id]
                print(f"     - {arm_id}: α={alpha}, β={beta}")
        
        # Test selection without category filtering
        print(f"\n🧪 Testing selection without category filtering:")
        context_no_category = {
            "safety_level": "standard",
            "target_format": "rego",
            "principle_complexity": 50
        }
        
        selected = await mab_service.mab_optimizer.select_optimal_prompt(context_no_category)
        if selected:
            print(f"✅ Selected (no category): {selected.name} ({selected.template_id})")
        else:
            print("❌ No template selected (no category)")
        
        # Test selection with each category
        categories = ["constitutional", "safety_critical", "fairness_aware", "adaptive"]
        
        for category in categories:
            print(f"\n🧪 Testing selection with category: {category}")
            
            context_with_category = {
                "category": category,
                "safety_level": "standard", 
                "target_format": "rego",
                "principle_complexity": 50
            }
            
            # Check available templates for this category
            available_templates = {
                tid: template for tid, template in mab_service.mab_optimizer.prompt_templates.items()
                if template.category == category
            }
            print(f"   Available templates for {category}: {list(available_templates.keys())}")
            
            # Try selection
            try:
                selected = await mab_service.mab_optimizer.select_optimal_prompt(context_with_category)
                if selected:
                    print(f"   ✅ Selected: {selected.name} ({selected.template_id})")
                else:
                    print(f"   ❌ No template selected for {category}")
            except Exception as e:
                print(f"   ❌ Error selecting template for {category}: {e}")
                
                # Debug the selection process
                print(f"   🔍 Debugging selection for {category}:")
                
                # Check what the MAB algorithm would select
                mab_service.mab_optimizer._update_available_arms(list(available_templates.keys()))
                selected_id = mab_service.mab_optimizer.mab_algorithm.select_arm(context_with_category)
                print(f"      MAB algorithm selected ID: {selected_id}")
                print(f"      Available template IDs: {list(available_templates.keys())}")
                print(f"      ID in available templates: {selected_id in available_templates}")
                
                # Check MAB algorithm arms after update
                if hasattr(mab_service.mab_optimizer.mab_algorithm, 'alpha'):
                    print(f"      MAB algorithm arms after update: {list(mab_service.mab_optimizer.mab_algorithm.alpha.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run debug test."""
    print("🚀 Starting MAB Template Selection Debug...")
    print("=" * 60)
    
    success = await debug_template_selection()
    
    if success:
        print("\n✅ Debug completed successfully!")
    else:
        print("\n❌ Debug failed!")
        
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
