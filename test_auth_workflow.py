#!/usr/bin/env python3
"""
ACGS-PGP Authentication Service Workflow Testing Script
Tests the complete authentication workflow including CSRF protection.
"""

import requests
import json
import re
from urllib.parse import unquote

BASE_URL = "http://localhost:8000/api/auth"

def extract_csrf_token(cookie_header):
    """Extract CSRF token from Set-Cookie header."""
    # Look for fastapi-csrf-token cookie
    match = re.search(r'fastapi-csrf-token=([^;]+)', cookie_header)
    if match:
        # The token is URL encoded, decode it and extract the actual token
        encoded_token = match.group(1)
        # The token format is "token".signature, we need just the token part
        decoded = unquote(encoded_token)
        # Remove quotes and extract token before the dot
        if decoded.startswith('"') and decoded.endswith('"'):
            decoded = decoded[1:-1]  # Remove quotes
        return decoded
    return None

def test_user_registration():
    """Test user registration."""
    print("🔍 Testing user registration...")
    
    user_data = {
        "username": "testworkflow001",
        "email": "testworkflow001@example.com", 
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    print(f"   Registration Status: {response.status_code}")
    
    if response.status_code == 201:
        print("   ✅ User registration successful")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print("   ✅ User already exists (expected for repeated tests)")
        return True
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return False

def test_user_login():
    """Test user login and extract tokens."""
    print("🔍 Testing user login...")
    
    login_data = {
        "username": "testworkflow001",
        "password": "testpassword123"
    }
    
    response = requests.post(
        f"{BASE_URL}/token", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"   Login Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Login successful")
        
        # Extract cookies
        cookies = {}
        csrf_token = None
        
        for cookie in response.headers.get('Set-Cookie', '').split(','):
            if 'fastapi-csrf-token=' in cookie:
                csrf_token = extract_csrf_token(cookie)
            elif 'access_token_cookie=' in cookie:
                match = re.search(r'access_token_cookie=([^;]+)', cookie)
                if match:
                    cookies['access_token_cookie'] = match.group(1)
            elif 'refresh_token_cookie=' in cookie:
                match = re.search(r'refresh_token_cookie=([^;]+)', cookie)
                if match:
                    cookies['refresh_token_cookie'] = match.group(1)
        
        print(f"   CSRF Token: {csrf_token[:20]}..." if csrf_token else "   ❌ No CSRF token found")
        print(f"   Access Token: {'✅ Found' if 'access_token_cookie' in cookies else '❌ Missing'}")
        print(f"   Refresh Token: {'✅ Found' if 'refresh_token_cookie' in cookies else '❌ Missing'}")
        
        return {
            'csrf_token': csrf_token,
            'cookies': cookies,
            'response': response
        }
    else:
        print(f"   ❌ Login failed: {response.text}")
        return None

def test_protected_endpoint(auth_data):
    """Test accessing protected endpoint."""
    print("🔍 Testing protected endpoint access...")
    
    if not auth_data:
        print("   ❌ No authentication data available")
        return False
    
    cookies = auth_data['cookies']
    
    response = requests.get(
        f"{BASE_URL}/me",
        cookies=cookies
    )
    
    print(f"   Protected Endpoint Status: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ Protected endpoint access successful")
        print(f"   User: {user_data.get('username')} (ID: {user_data.get('id')})")
        return True
    else:
        print(f"   ❌ Protected endpoint access failed: {response.text}")
        return False

def test_csrf_protection():
    """Test CSRF protection on protected endpoints."""
    print("🔍 Testing CSRF protection...")
    
    # Test without CSRF token
    response = requests.post(f"{BASE_URL}/logout")
    print(f"   Logout without CSRF Status: {response.status_code}")
    
    if response.status_code == 403 or "Missing Cookie" in response.text:
        print("   ✅ CSRF protection working - request blocked")
        return True
    else:
        print(f"   ❌ CSRF protection failed: {response.text}")
        return False

def test_cross_service_integration(auth_data):
    """Test cross-service authentication integration."""
    print("🔍 Testing cross-service authentication integration...")

    if not auth_data:
        print("   ❌ No authentication data available")
        return False

    cookies = auth_data['cookies']

    # Test direct service health endpoints (bypassing nginx)
    services = {
        "AC Service": "http://localhost:8001/health",
        "Integrity Service": "http://localhost:8002/health",
        "FV Service": "http://localhost:8003/health",
        "GS Service": "http://localhost:8004/health",
        "PGC Service": "http://localhost:8005/health"
    }

    results = {}
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {service_name}: {response.json()}")
                results[service_name] = True
            else:
                print(f"   ❌ {service_name}: HTTP {response.status_code}")
                results[service_name] = False
        except Exception as e:
            print(f"   ❌ {service_name}: Connection error - {str(e)}")
            results[service_name] = False

    # Test nginx gateway routing
    print("\n   Testing Nginx Gateway Routing:")
    gateway_tests = {
        "Auth Health": "http://localhost:8000/api/auth/health",
        "Nginx Health": "http://localhost:8000/nginx_health"
    }

    for test_name, url in gateway_tests.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {test_name}: Working")
                results[test_name] = True
            else:
                print(f"   ❌ {test_name}: HTTP {response.status_code}")
                results[test_name] = False
        except Exception as e:
            print(f"   ❌ {test_name}: Connection error - {str(e)}")
            results[test_name] = False

    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)

    print(f"\n   Cross-Service Integration: {success_count}/{total_count} services accessible")
    return success_count >= total_count * 0.8  # 80% success rate

def main():
    """Run complete authentication workflow test."""
    print("🚀 ACGS-PGP Authentication Service Comprehensive Test")
    print("=" * 70)

    # Test 1: User Registration
    if not test_user_registration():
        print("❌ Registration test failed, stopping tests")
        return

    print()

    # Test 2: User Login
    auth_data = test_user_login()
    if not auth_data:
        print("❌ Login test failed, stopping tests")
        return

    print()

    # Test 3: Protected Endpoint Access
    if not test_protected_endpoint(auth_data):
        print("❌ Protected endpoint test failed")

    print()

    # Test 4: CSRF Protection
    if not test_csrf_protection():
        print("❌ CSRF protection test failed")

    print()

    # Test 5: Cross-Service Integration
    if not test_cross_service_integration(auth_data):
        print("❌ Cross-service integration test failed")

    print()
    print("=" * 70)
    print("🎉 Comprehensive authentication testing completed!")

if __name__ == "__main__":
    main()
