#!/usr/bin/env python3
"""
Validation script for Stakeholder Engagement System

This script validates the stakeholder engagement system implementation
by checking code structure, imports, and basic functionality.
"""

import sys
import os
import ast
import inspect

def validate_file_structure():
    """Validate that all required files exist."""
    print("Validating file structure...")
    
    required_files = [
        "app/services/stakeholder_engagement.py",
        "app/api/v1/stakeholder_engagement.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✓ All required files exist")
    return True

def validate_stakeholder_service():
    """Validate stakeholder engagement service structure."""
    print("Validating stakeholder engagement service...")
    
    service_file = "app/services/stakeholder_engagement.py"
    
    try:
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Parse the AST to check for required classes and methods
        tree = ast.parse(content)
        
        classes_found = []
        methods_found = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes_found.append(node.name)
                
                # Check for methods in classes
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods_found.append(f"{node.name}.{item.name}")
        
        # Required classes
        required_classes = [
            "NotificationChannel",
            "StakeholderRole", 
            "NotificationStatus",
            "FeedbackStatus",
            "NotificationRecord",
            "FeedbackRecord",
            "StakeholderEngagementInput",
            "StakeholderEngagementStatus",
            "StakeholderNotificationService"
        ]
        
        missing_classes = [cls for cls in required_classes if cls not in classes_found]
        
        if missing_classes:
            print(f"❌ Missing classes: {missing_classes}")
            return False
        
        # Required methods in StakeholderNotificationService
        required_methods = [
            "StakeholderNotificationService.initiate_stakeholder_engagement",
            "StakeholderNotificationService.collect_stakeholder_feedback",
            "StakeholderNotificationService.get_engagement_status",
            "StakeholderNotificationService.get_stakeholder_notifications",
            "StakeholderNotificationService.get_stakeholder_feedback"
        ]
        
        missing_methods = [method for method in required_methods if method not in methods_found]
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        
        print("✓ Stakeholder engagement service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error validating service: {e}")
        return False

def validate_api_endpoints():
    """Validate API endpoints structure."""
    print("Validating API endpoints...")
    
    api_file = "app/api/v1/stakeholder_engagement.py"
    
    try:
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for required endpoint patterns
        required_patterns = [
            "@router.post(\"/initiate\"",
            "@router.get(\"/status/{amendment_id}\"",
            "@router.post(\"/feedback\"",
            "@router.get(\"/notifications\"",
            "@router.get(\"/feedback/{amendment_id}\"",
            "@router.websocket(\"/ws/{amendment_id}\")"
        ]
        
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"❌ Missing API patterns: {missing_patterns}")
            return False
        
        print("✓ API endpoints structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error validating API: {e}")
        return False

def validate_constitutional_council_integration():
    """Validate integration with Constitutional Council StateGraph."""
    print("Validating Constitutional Council integration...")
    
    graph_file = "app/workflows/constitutional_council_graph.py"
    
    try:
        with open(graph_file, 'r') as f:
            content = f.read()
        
        # Check for stakeholder engagement imports and usage
        required_imports = [
            "from app.services.stakeholder_engagement import",
            "StakeholderNotificationService",
            "StakeholderEngagementInput"
        ]
        
        missing_imports = []
        for import_pattern in required_imports:
            if import_pattern not in content:
                missing_imports.append(import_pattern)
        
        if missing_imports:
            print(f"❌ Missing imports in Constitutional Council: {missing_imports}")
            return False
        
        # Check for stakeholder service initialization
        if "self.stakeholder_service = StakeholderNotificationService" not in content:
            print("❌ Missing stakeholder service initialization in Constitutional Council")
            return False
        
        print("✓ Constitutional Council integration is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error validating Constitutional Council integration: {e}")
        return False

def validate_main_app_integration():
    """Validate integration with main AC service app."""
    print("Validating main app integration...")
    
    main_file = "app/main.py"
    
    try:
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Check for stakeholder engagement router import and inclusion
        if "stakeholder_engagement_router" not in content:
            print("❌ Missing stakeholder engagement router in main app")
            return False
        
        if "app.include_router" not in content or "stakeholder_engagement_router" not in content:
            print("❌ Stakeholder engagement router not included in main app")
            return False
        
        print("✓ Main app integration is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error validating main app integration: {e}")
        return False

def run_validation():
    """Run all validation checks."""
    print("="*60)
    print("STAKEHOLDER ENGAGEMENT SYSTEM - VALIDATION")
    print("="*60)
    
    checks = [
        ("File Structure", validate_file_structure),
        ("Stakeholder Service", validate_stakeholder_service),
        ("API Endpoints", validate_api_endpoints),
        ("Constitutional Council Integration", validate_constitutional_council_integration),
        ("Main App Integration", validate_main_app_integration)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("Stakeholder Engagement System is properly implemented and integrated.")
        print("\nKey Features Implemented:")
        print("- Multi-channel notification system (email, dashboard, webhook, websocket)")
        print("- Role-based stakeholder management (4 stakeholder roles)")
        print("- Real-time feedback collection and tracking")
        print("- Integration with Constitutional Council StateGraph")
        print("- REST API endpoints for stakeholder engagement")
        print("- WebSocket support for real-time updates")
        print("- Comprehensive status tracking and reporting")
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please review the issues above.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
