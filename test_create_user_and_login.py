#!/usr/bin/env python3
"""
Test script to create a user via API and then test login
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def create_test_user():
    """Create a test user via the API"""
    url = f"{BASE_URL}/users/"
    
    payload = {
        "first_name": "Test",
        "last_name": "User", 
        "email": "test@example.com",
        "password": "demo"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Creating user at: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nCreate User Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_json = response.json()
                print(f"Create User Response: {json.dumps(response_json, indent=2)}")
                return response.status_code in [200, 201]
            except:
                print(f"Create User Response Text: {response.text}")
                return False
        else:
            print(f"Create User Response Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR creating user: {e}")
        return False

def test_login():
    """Test login with the created user"""
    url = f"{BASE_URL}/users/login"
    
    payload = {
        "email": "test@example.com", 
        "password": "demo"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"\nTesting login at: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nLogin Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_json = response.json()
                print(f"Login Response: {json.dumps(response_json, indent=2)}")
                
                # Check if login was successful
                if response.status_code == 200 and 'access_token' in response_json:
                    print("✅ LOGIN SUCCESSFUL!")
                    return True
                else:
                    print("❌ LOGIN FAILED")
                    return False
            except:
                print(f"Login Response Text: {response.text}")
                return False
        else:
            print(f"Login Response Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR during login: {e}")
        return False

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Server root endpoint status: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("ERROR: Server is not running or not accessible at localhost:8000")
        return False
    except Exception as e:
        print(f"ERROR testing server: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing User Creation and Login ===")
    
    if not test_server_availability():
        print("Cannot proceed - server not available")
        exit(1)
    
    print("\n=== Step 1: Creating Test User ===")
    if create_test_user():
        print("\n=== Step 2: Testing Login ===")
        if test_login():
            print("\n🎉 SUCCESS: Login functionality is working correctly!")
        else:
            print("\n❌ ISSUE: Login failed even with valid credentials")
    else:
        print("\n❌ ISSUE: Could not create test user")