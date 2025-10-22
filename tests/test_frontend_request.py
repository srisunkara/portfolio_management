#!/usr/bin/env python3
import requests

# Test exactly what the frontend would send
url = "http://localhost:8000/users/login"

print("Testing frontend-style request with Authorization header...")
print(f"URL: {url}")

# First test preflight with Authorization header requested
try:
    response = requests.options(
        url,
        headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type,authorization'  # This is what frontend would request
        }
    )
    
    print(f"Preflight Status Code: {response.status_code}")
    print("Preflight Response Headers:")
    for header, value in response.headers.items():
        if 'access-control' in header.lower():
            print(f"  {header}: {value}")
    print(f"Response Body: {response.text}")
    
    print(f"\nPreflight Success: {200 <= response.status_code < 300}")
    
except requests.exceptions.RequestException as e:
    print(f"Preflight Request failed: {e}")

print("\n" + "="*50)

# Now test actual POST with Authorization header (empty token case)
print("Testing POST request with Authorization header (no token)...")
try:
    response = requests.post(
        url,
        headers={
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:5173'
            # Note: No Authorization header since no token in localStorage
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

print("\n" + "="*50)

# Test with empty Authorization header that frontend might send
print("Testing POST request with empty Authorization header...")
try:
    response = requests.post(
        url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': '',  # Empty auth header
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