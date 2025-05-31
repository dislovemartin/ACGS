#!/usr/bin/env python3
"""
Debug CSRF token handling
"""

import requests
import re
import base64
from urllib.parse import unquote

BASE_URL = "http://localhost:8000/api/auth"

def debug_csrf_flow():
    """Debug the complete CSRF flow."""
    print("🔍 Debugging CSRF token flow...")
    
    # Step 1: Login and get tokens
    print("\n1. Login to get tokens...")
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
    
    if response.status_code != 200:
        print(f"   Login failed: {response.text}")
        return
    
    # Extract all cookies
    set_cookie_header = response.headers.get('Set-Cookie', '')
    print(f"   Set-Cookie header: {set_cookie_header}")
    
    # Parse cookies manually
    cookies = {}
    csrf_cookie_raw = None
    
    for cookie in set_cookie_header.split(','):
        if 'fastapi-csrf-token=' in cookie:
            match = re.search(r'fastapi-csrf-token=([^;]+)', cookie)
            if match:
                csrf_cookie_raw = match.group(1)
                cookies['fastapi-csrf-token'] = csrf_cookie_raw
        elif 'access_token_cookie=' in cookie:
            match = re.search(r'access_token_cookie=([^;]+)', cookie)
            if match:
                cookies['access_token_cookie'] = match.group(1)
        elif 'refresh_token_cookie=' in cookie:
            match = re.search(r'refresh_token_cookie=([^;]+)', cookie)
            if match:
                cookies['refresh_token_cookie'] = match.group(1)
    
    print(f"   Parsed cookies: {list(cookies.keys())}")
    print(f"   CSRF cookie raw: {csrf_cookie_raw}")
    
    # Step 2: Extract CSRF token
    print("\n2. Extract CSRF token...")
    if csrf_cookie_raw:
        decoded = unquote(csrf_cookie_raw)
        print(f"   URL decoded: {decoded}")
        
        token_part = decoded.split('.')[0]
        print(f"   Token part: {token_part}")
        
        try:
            # Add padding if needed
            padding = 4 - (len(token_part) % 4)
            if padding != 4:
                token_part += '=' * padding
            
            decoded_bytes = base64.b64decode(token_part)
            decoded_token = decoded_bytes.decode('utf-8')
            print(f"   Decoded token: {decoded_token}")
            
            # Remove quotes
            if decoded_token.startswith('"') and decoded_token.endswith('"'):
                actual_token = decoded_token[1:-1]
            else:
                actual_token = decoded_token
            
            print(f"   Actual CSRF token: {actual_token}")
            
        except Exception as e:
            print(f"   Error decoding: {e}")
            return
    else:
        print("   No CSRF cookie found")
        return
    
    # Step 3: Test refresh endpoint with different approaches
    print("\n3. Test refresh endpoint...")
    
    # Approach 1: Use the raw cookie value as X-CSRF-Token
    print("   Approach 1: Raw cookie value as header...")
    response1 = requests.post(
        f"{BASE_URL}/token/refresh",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_cookie_raw
        },
        cookies=cookies,
        timeout=5
    )
    print(f"   Status: {response1.status_code}, Response: {response1.text[:100]}")
    
    # Approach 2: Use the decoded token as X-CSRF-Token
    print("   Approach 2: Decoded token as header...")
    response2 = requests.post(
        f"{BASE_URL}/token/refresh",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": actual_token
        },
        cookies=cookies,
        timeout=5
    )
    print(f"   Status: {response2.status_code}, Response: {response2.text[:100]}")
    
    # Approach 3: Use the URL decoded value as X-CSRF-Token
    print("   Approach 3: URL decoded value as header...")
    response3 = requests.post(
        f"{BASE_URL}/token/refresh",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": decoded
        },
        cookies=cookies,
        timeout=5
    )
    print(f"   Status: {response3.status_code}, Response: {response3.text[:100]}")

if __name__ == "__main__":
    debug_csrf_flow()
