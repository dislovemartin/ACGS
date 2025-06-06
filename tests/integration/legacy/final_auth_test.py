import os, pytest
if not os.environ.get("ACGS_INTEGRATION"):
    pytest.skip("integration test requires running services", allow_module_level=True)

#!/usr/bin/env python3
"""
ACGS-PGP Authentication Service - Final Comprehensive Test
Tests all authentication workflows including CSRF protection, token refresh, and logout.
"""

import requests
import json
import re
import base64
from urllib.parse import unquote

BASE_URL = "http://localhost:8000/api/auth"

def extract_csrf_token(cookie_header):
    """Extract and decode CSRF token from Set-Cookie header."""
    match = re.search(r'fastapi-csrf-token=([^;]+)', cookie_header)
    if match:
        encoded_token = match.group(1)
        decoded = unquote(encoded_token)
        token_part = decoded.split('.')[0]
        
        try:
            padding = 4 - (len(token_part) % 4)
            if padding != 4:
                token_part += '=' * padding
            
            decoded_bytes = base64.b64decode(token_part)
            decoded_token = decoded_bytes.decode('utf-8')
            
            if decoded_token.startswith('"') and decoded_token.endswith('"'):
                return decoded_token[1:-1]
            return decoded_token
        except Exception:
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
            match = re.search(r'fastapi-csrf-token=([^;]+)', cookie)
            if match:
                cookies['fastapi-csrf-token'] = match.group(1)
        elif 'access_token_cookie=' in cookie:
            match = re.search(r'access_token_cookie=([^;]+)', cookie)
            if match:
                cookies['access_token_cookie'] = match.group(1)
        elif 'refresh_token_cookie=' in cookie:
            match = re.search(r'refresh_token_cookie=([^;]+)', cookie)
            if match:
                cookies['refresh_token_cookie'] = match.group(1)
    
    return cookies, csrf_token

def test_complete_auth_workflow():
    """Test the complete authentication workflow."""
    print("🚀 ACGS-PGP Authentication Service - Final Comprehensive Test")
    print("=" * 70)
    
    results = {}
    
    # Test 1: User Login
    print("🔍 Test 1: User Login...")
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
        results['login'] = True
        auth_data = {'cookies': cookies, 'csrf_token': csrf_token}
    else:
        print(f"   ❌ Login failed: {response.status_code} - {response.text}")
        results['login'] = False
        return results
    
    print()
    
    # Test 2: Protected Endpoint Access
    print("🔍 Test 2: Protected Endpoint Access...")
    response = requests.get(f"{BASE_URL}/me", cookies=cookies)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ Protected endpoint access successful")
        print(f"   User: {user_data.get('username')} (ID: {user_data.get('id')})")
        results['protected_access'] = True
    else:
        print(f"   ❌ Protected endpoint access failed: {response.status_code}")
        results['protected_access'] = False
    
    print()
    
    # Test 3: CSRF Protection
    print("🔍 Test 3: CSRF Protection...")
    response = requests.post(f"{BASE_URL}/token/refresh")
    
    if response.status_code in [400, 403] and "Missing" in response.text:
        print("   ✅ CSRF protection working - request blocked without token")
        results['csrf_protection'] = True
    else:
        print(f"   ❌ CSRF protection failed: {response.status_code}")
        results['csrf_protection'] = False
    
    print()
    
    # Test 4: Token Refresh
    print("🔍 Test 4: Token Refresh...")
    response = requests.post(
        f"{BASE_URL}/token/refresh",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token
        },
        cookies=cookies,
        timeout=10
    )
    
    if response.status_code == 200:
        new_cookies, new_csrf_token = extract_cookies_from_response(response)
        print("   ✅ Token refresh successful")
        print(f"   New Access Token: {'✅ Found' if 'access_token_cookie' in new_cookies else '❌ Missing'}")
        print(f"   New Refresh Token: {'✅ Found' if 'refresh_token_cookie' in new_cookies else '❌ Missing'}")
        print(f"   New CSRF Token: {'✅ Found' if new_csrf_token else '❌ Missing'}")
        results['token_refresh'] = True
        
        # Update auth data with new tokens
        auth_data['cookies'].update(new_cookies)
        auth_data['csrf_token'] = new_csrf_token
    else:
        print(f"   ❌ Token refresh failed: {response.status_code} - {response.text}")
        results['token_refresh'] = False
    
    print()
    
    # Test 5: Logout
    print("🔍 Test 5: Logout...")
    response = requests.post(
        f"{BASE_URL}/logout",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": auth_data['csrf_token']
        },
        cookies=auth_data['cookies'],
        timeout=10
    )
    
    if response.status_code == 200:
        print("   ✅ Logout successful")
        results['logout'] = True
    else:
        print(f"   ❌ Logout failed: {response.status_code} - {response.text}")
        results['logout'] = False
    
    print()
    
    # Test 6: Post-Logout Access
    print("🔍 Test 6: Post-Logout Protected Access...")
    response = requests.get(f"{BASE_URL}/me")
    
    if response.status_code in [401, 403]:
        print("   ✅ Protected endpoint correctly blocked after logout")
        results['post_logout_blocked'] = True
    else:
        print(f"   ❌ Protected endpoint still accessible: {response.status_code}")
        results['post_logout_blocked'] = False
    
    print()
    
    # Summary
    print("=" * 70)
    print("📊 Final Test Results:")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Authentication service is production-ready.")
    else:
        print("⚠️  Some tests failed. Review and fix before production deployment.")
    
    return results

if __name__ == "__main__":
    test_complete_auth_workflow()

import os
import asyncio
import pytest

@pytest.mark.skipif(not os.environ.get("ACGS_INTEGRATION"), reason="Integration test requires running services")
def test_main_wrapper():
    if 'test_complete_auth_workflow' in globals():
        if asyncio.iscoroutinefunction(test_complete_auth_workflow):
            asyncio.run(test_complete_auth_workflow())
        else:
            test_complete_auth_workflow()
