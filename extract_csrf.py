#!/usr/bin/env python3
import base64
import json

# The CSRF cookie value from the login response
csrf_cookie = "ImZkZTliODljNjVkZTRlZWRmZmIwMmI4ZTRlZWUyNTRhZWQ5NGIwYmIi.aDpI2Q._40Qru_FQeSqKc9xkkX_VuSzoqY"

print(f"Original CSRF cookie: {csrf_cookie}")

# Split by dots - fastapi-csrf-protect format is: token.timestamp.signature
parts = csrf_cookie.split('.')
print(f"Parts: {parts}")

if len(parts) >= 1:
    token_part = parts[0]
    print(f"Token part: {token_part}")
    
    try:
        # Decode base64 - the token part is base64 encoded
        # Add padding if needed
        padding = 4 - (len(token_part) % 4)
        if padding != 4:
            token_part += '=' * padding
            
        decoded_bytes = base64.b64decode(token_part)
        decoded_token = decoded_bytes.decode('utf-8')
        print(f"Decoded token: {decoded_token}")
        
        # Remove quotes if present
        if decoded_token.startswith('"') and decoded_token.endswith('"'):
            actual_token = decoded_token[1:-1]
        else:
            actual_token = decoded_token
            
        print(f"Actual CSRF token: {actual_token}")
        
    except Exception as e:
        print(f"Error decoding: {e}")
