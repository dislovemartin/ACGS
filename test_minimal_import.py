#!/usr/bin/env python3
"""
Minimal import test for ACGS-PGP services
Tests basic FastAPI functionality without complex dependencies
"""

import sys
import os
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

def test_basic_imports():
    """Test basic Python imports"""
    print("=== Testing Basic Imports ===")
    
    try:
        import fastapi
        print("✅ FastAPI imported")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import httpx
        print("✅ HTTPX imported")
    except ImportError as e:
        print(f"❌ HTTPX import failed: {e}")
        return False
    
    return True

def test_minimal_fastapi():
    """Test minimal FastAPI app creation"""
    print("\n=== Testing Minimal FastAPI App ===")
    
    try:
        from fastapi import FastAPI
        
        app = FastAPI(title="Test Service")
        
        @app.get("/")
        async def root():
            return {"message": "Test service is running"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        print("✅ Minimal FastAPI app created successfully")
        print(f"✅ App title: {app.title}")
        print(f"✅ Routes: {len(app.routes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Minimal FastAPI app creation failed: {e}")
        return False

def test_service_imports():
    """Test individual service imports with timeout"""
    print("\n=== Testing Service Imports ===")
    
    services = [
        ("auth_service", "auth_service"),
        ("ac_service", "ac_service"),
        ("integrity_service", "integrity_service"),
        ("fv_service", "fv_service"),
        ("gs_service", "gs_service"),
        ("ec_service", "ec_service"),
    ]
    
    results = {}
    
    for service_name, service_dir in services:
        print(f"\nTesting {service_name}...")
        start_time = time.time()
        
        try:
            # Change to service directory
            service_path = backend_path / service_dir
            if not service_path.exists():
                print(f"  ❌ Service directory not found: {service_path}")
                results[service_name] = "directory_not_found"
                continue
            
            # Add service to path
            sys.path.insert(0, str(service_path))
            
            # Try to import main module
            try:
                from app.main import app
                import_time = time.time() - start_time
                print(f"  ✅ SUCCESS - Imported in {import_time:.2f}s")
                print(f"  ✅ FastAPI app: {hasattr(app, 'title')}")
                if hasattr(app, 'title'):
                    print(f"  ✅ App title: {app.title}")
                results[service_name] = "success"
                
            except ImportError as e:
                import_time = time.time() - start_time
                print(f"  ❌ Import failed after {import_time:.2f}s")
                print(f"  Error: {str(e)[:100]}...")
                results[service_name] = f"import_error: {str(e)[:50]}"
                
            except Exception as e:
                import_time = time.time() - start_time
                print(f"  ❌ Unexpected error after {import_time:.2f}s")
                print(f"  Error: {str(e)[:100]}...")
                results[service_name] = f"unexpected_error: {str(e)[:50]}"
            
            # Clean up imports to avoid conflicts
            modules_to_remove = [k for k in sys.modules.keys() if k.startswith('app')]
            for mod in modules_to_remove:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Remove service path
            if str(service_path) in sys.path:
                sys.path.remove(str(service_path))
                
        except Exception as e:
            import_time = time.time() - start_time
            print(f"  ❌ Setup failed after {import_time:.2f}s")
            print(f"  Error: {str(e)}")
            results[service_name] = f"setup_error: {str(e)[:50]}"
    
    return results

def main():
    """Main test function"""
    print("ACGS-PGP Service Import Testing")
    print("=" * 50)
    
    # Test basic imports
    if not test_basic_imports():
        print("\n❌ Basic imports failed - cannot proceed")
        return 1
    
    # Test minimal FastAPI
    if not test_minimal_fastapi():
        print("\n❌ Minimal FastAPI test failed")
        return 1
    
    # Test service imports
    results = test_service_imports()
    
    # Summary
    print("\n" + "=" * 50)
    print("IMPORT TEST SUMMARY")
    print("=" * 50)
    
    success_count = 0
    for service, result in results.items():
        status = "✅" if result == "success" else "❌"
        print(f"{status} {service}: {result}")
        if result == "success":
            success_count += 1
    
    print(f"\nSuccess Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    if success_count == len(results):
        print("🎉 All services imported successfully!")
        return 0
    else:
        print("⚠️  Some services failed to import")
        return 1

if __name__ == "__main__":
    exit(main())
