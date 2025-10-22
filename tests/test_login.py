#!/usr/bin/env python3
"""
Test script to reproduce login issue by making HTTP requests to the backend directly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    # Test the login endpoint that the frontend is trying to call
    url = f"{BASE_URL}/users/login"
    
    # Same payload format that the frontend sends
    payload = {
        "email": "test@example.com", 
        "password": "demo"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Testing login at: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
        else:
            print(f"Response Text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")

def test_server_availability():
    """Test if the server is running at all"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Server root endpoint status: {response.status_code}")
        print(f"Server root response: {response.text}")
        return True
    except requests.exceptions.ConnectionError:
        print("ERROR: Server is not running or not accessible at localhost:8000")
        return False
    except Exception as e:
        print(f"ERROR testing server: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Login Issue ===")
    
    if test_server_availability():
        print("\n=== Testing Login Endpoint ===")
        test_login()
    else:
        print("Cannot test login - server not available")