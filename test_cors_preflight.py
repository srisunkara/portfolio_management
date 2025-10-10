#!/usr/bin/env python3
import requests

# Test CORS preflight request to login endpoint
url = "http://localhost:8000/users/login"

print("Testing CORS preflight (OPTIONS) request...")
print(f"URL: {url}")

try:
    # Send preflight OPTIONS request
    response = requests.options(
        url,
        headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type'
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    for header, value in response.headers.items():
        print(f"  {header}: {value}")
    print(f"Response Body: {response.text}")
    
    # Check specific CORS headers
    cors_headers = [
        'Access-Control-Allow-Origin',
        'Access-Control-Allow-Methods', 
        'Access-Control-Allow-Headers',
        'Access-Control-Allow-Credentials'
    ]
    
    print("\nCORS Headers Check:")
    for header in cors_headers:
        value = response.headers.get(header, 'NOT PRESENT')
        print(f"  {header}: {value}")
        
    print(f"\nPreflight Success: {200 <= response.status_code < 300}")
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")

print("\n" + "="*50)

print("Testing actual POST request...")
try:
    response = requests.post(
        url,
        headers={
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:5173'
        },
        json={
            'email': 'test@example.com',
            'password': 'demo'
        }
    )
    
    print(f"POST Status Code: {response.status_code}")
    print("POST Response Headers:")
    for header, value in response.headers.items():
        if 'access-control' in header.lower():
            print(f"  {header}: {value}")
    print(f"POST Response Body: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"POST Request failed: {e}")