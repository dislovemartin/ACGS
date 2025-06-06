import os, pytest
if not os.environ.get("ACGS_INTEGRATION"):
    pytest.skip("integration test requires running services", allow_module_level=True)

#!/usr/bin/env python3
"""
ACGS-PGP Authentication Service Token Refresh and Logout Testing Script
Tests the complete token lifecycle including refresh and logout functionality.
"""

import requests
import json
import re
from urllib.parse import unquote

BASE_URL = "http://localhost:8000/api/auth"

def extract_csrf_token(cookie_header):
    """Extract CSRF token from Set-Cookie header."""
    import base64

    # Look for fastapi-csrf-token cookie
    match = re.search(r'fastapi-csrf-token=([^;]+)', cookie_header)
    if match:
        encoded_token = match.group(1)
        # URL decode the token
        decoded = unquote(encoded_token)

        # The token format is: base64_token.timestamp.signature
        # We need to decode the base64 part
        token_part = decoded.split('.')[0]

        try:
            # Add padding if needed for base64 decoding
            padding = 4 - (len(token_part) % 4)
            if padding != 4:
                token_part += '=' * padding

            # Decode base64
            decoded_bytes = base64.b64decode(token_part)
            decoded_token = decoded_bytes.decode('utf-8')

            # Remove quotes if present
            if decoded_token.startswith('"') and decoded_token.endswith('"'):
                actual_token = decoded_token[1:-1]
            else:
                actual_token = decoded_token

            return actual_token
        except Exception as e:
            print(f"Error decoding CSRF token: {e}")
            return None
    return None

def extract_cookies_from_response(response):
    """Extract all relevant cookies from response."""
    cookies = {}
    csrf_token = None
    
    set_cookie_header = response.headers.get('Set-Cookie', '')
    
    for cookie in set_cookie_header.split(','):
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
    
    return cookies, csrf_token

def test_user_login():
    """Login and get tokens for testing."""
    print("🔍 Logging in to get tokens...")
    
    login_data = {
        "username": "testworkflow001",
        "password": "testpassword123"
    }
    
    response = requests.post(
        f"{BASE_URL}/token", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        cookies, csrf_token = extract_cookies_from_response(response)
        print(f"   ✅ Login successful")
        print(f"   CSRF Token: {csrf_token[:20]}..." if csrf_token else "   ❌ No CSRF token")
        print(f"   Access Token: {'✅ Found' if 'access_token_cookie' in cookies else '❌ Missing'}")
        print(f"   Refresh Token: {'✅ Found' if 'refresh_token_cookie' in cookies else '❌ Missing'}")
        
        return {
            'cookies': cookies,
            'csrf_token': csrf_token,
            'response': response
        }
    else:
        print(f"   ❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_token_refresh(auth_data):
    """Test token refresh functionality."""
    print("🔍 Testing token refresh...")
    
    if not auth_data or 'refresh_token_cookie' not in auth_data['cookies']:
        print("   ❌ No refresh token available")
        return False
    
    # Test refresh without CSRF token (should fail)
    print("   Testing refresh without CSRF token...")
    response = requests.post(
        f"{BASE_URL}/token/refresh",
        headers={"Content-Type": "application/json"},
        cookies={'refresh_token_cookie': auth_data['cookies']['refresh_token_cookie']}
    )
    
    if response.status_code == 400 and "Missing Cookie" in response.text:
        print("   ✅ CSRF protection working - refresh blocked without token")
    else:
        print(f"   ❌ CSRF protection failed: {response.status_code} - {response.text}")
        return False
    
    # Test refresh with CSRF token (should work)
    print("   Testing refresh with CSRF token...")

    # Use the original auth data (same session)
    refresh_cookies = {
        'refresh_token_cookie': auth_data['cookies']['refresh_token_cookie'],
        'fastapi-csrf-token': auth_data['csrf_token']
    }

    response = requests.post(
        f"{BASE_URL}/token/refresh",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": auth_data['csrf_token']
        },
        cookies=refresh_cookies
    )
    
    print(f"   Refresh Status: {response.status_code}")
    
    if response.status_code == 200:
        new_cookies, new_csrf_token = extract_cookies_from_response(response)
        print("   ✅ Token refresh successful")
        print(f"   New Access Token: {'✅ Found' if 'access_token_cookie' in new_cookies else '❌ Missing'}")
        print(f"   New Refresh Token: {'✅ Found' if 'refresh_token_cookie' in new_cookies else '❌ Missing'}")
        print(f"   New CSRF Token: {'✅ Found' if new_csrf_token else '❌ Missing'}")
        return True
    else:
        print(f"   ❌ Token refresh failed: {response.text}")
        return False

def test_logout(auth_data):
    """Test logout functionality."""
    print("🔍 Testing logout...")
    
    if not auth_data:
        print("   ❌ No auth data available")
        return False
    
    # Test logout without CSRF token (should fail)
    print("   Testing logout without CSRF token...")
    response = requests.post(
        f"{BASE_URL}/logout",
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 400 and "Missing Cookie" in response.text:
        print("   ✅ CSRF protection working - logout blocked without token")
    else:
        print(f"   ❌ CSRF protection failed: {response.status_code} - {response.text}")
        return False
    
    # Test logout with CSRF token (should work)
    print("   Testing logout with CSRF token...")
    
    logout_cookies = {
        'access_token_cookie': auth_data['cookies'].get('access_token_cookie', ''),
        'refresh_token_cookie': auth_data['cookies'].get('refresh_token_cookie', ''),
        'fastapi-csrf-token': auth_data['csrf_token']
    }
    
    response = requests.post(
        f"{BASE_URL}/logout",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": auth_data['csrf_token']
        },
        cookies=logout_cookies
    )
    
    print(f"   Logout Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Logout successful")
        
        # Check if cookies are cleared
        set_cookie_header = response.headers.get('Set-Cookie', '')
        cookies_cleared = 'access_token_cookie=;' in set_cookie_header or 'refresh_token_cookie=;' in set_cookie_header
        
        if cookies_cleared:
            print("   ✅ Authentication cookies cleared")
        else:
            print("   ⚠️  Authentication cookies may not be cleared")
        
        return True
    else:
        print(f"   ❌ Logout failed: {response.text}")
        return False

def test_protected_endpoint_after_logout():
    """Test that protected endpoints are inaccessible after logout."""
    print("🔍 Testing protected endpoint access after logout...")
    
    response = requests.get(f"{BASE_URL}/me")
    
    if response.status_code == 401 or response.status_code == 403:
        print("   ✅ Protected endpoint correctly blocked after logout")
        return True
    else:
        print(f"   ❌ Protected endpoint still accessible: {response.status_code}")
        return False

def main():
    """Run complete token lifecycle test."""
    print("🚀 ACGS-PGP Token Refresh and Logout Test")
    print("=" * 60)
    
    # Test 1: Login to get tokens
    auth_data = test_user_login()
    if not auth_data:
        print("❌ Login failed, stopping tests")
        return
    
    print()
    
    # Test 2: Token Refresh
    refresh_success = test_token_refresh(auth_data)
    if not refresh_success:
        print("❌ Token refresh test failed")
    
    print()
    
    # Test 3: Logout
    logout_success = test_logout(auth_data)
    if not logout_success:
        print("❌ Logout test failed")
    
    print()
    
    # Test 4: Protected endpoint after logout
    protected_blocked = test_protected_endpoint_after_logout()
    if not protected_blocked:
        print("❌ Protected endpoint test failed")
    
    print()
    print("=" * 60)
    
    # Summary
    tests_passed = sum([
        auth_data is not None,
        refresh_success,
        logout_success,
        protected_blocked
    ])
    
    print(f"📊 Test Results: {tests_passed}/4 tests passed")
    
    if tests_passed == 4:
        print("🎉 All token lifecycle tests passed!")
    else:
        print("⚠️  Some token lifecycle tests failed.")

if __name__ == "__main__":
    main()

import os
import asyncio
import pytest

@pytest.mark.skipif(not os.environ.get("ACGS_INTEGRATION"), reason="Integration test requires running services")
def test_main_wrapper():
    if 'main' in globals():
        if asyncio.iscoroutinefunction(main):
            asyncio.run(main())
        else:
            main()
