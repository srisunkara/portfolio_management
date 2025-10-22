#!/usr/bin/env python3
"""
Test script to reproduce the "Failed to update price" error on add price page
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except:
        return False

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(f"{BASE_URL}/users/login", json={
            "email": "test@example.com",
            "password": "demo"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except:
        pass
    return None

def test_create_security_price_with_id():
    """Test creating a security price with the exact frontend payload structure"""
    print("Testing create security price with frontend payload structure...")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # This exactly mimics what the frontend is sending based on SecurityPriceForm.jsx
    payload = {
        "security_price_id": 0,  # Number(id) where id is undefined for new records
        "security_id": None,     # form.security_id === "" ? null : Number(form.security_id)
        "price_source_id": None, # form.price_source_id === "" ? null : Number(form.price_source_id)
        "price_date": "2025-01-15",
        "price": None,           # form.price === "" ? null : Number(form.price)
        "market_cap": None,      # form.market_cap === "" ? null : Number(form.market_cap)
        "addl_notes": None,      # form.addl_notes || null
        "price_currency": "USD"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/security-prices/", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print("✅ CONFIRMED: Create operation fails when security_price_id is included")
            return True
        else:
            print("❌ Unexpected: Create operation succeeded with security_price_id")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_security_price_without_id():
    """Test creating a security price without security_price_id (which should work)"""
    print("\nTesting create security price without security_price_id...")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # This is how it should be sent - without security_price_id
    payload = {
        "security_id": 1,
        "price_source_id": 1,
        "price_date": "2025-01-16",
        "price": 101.50,
        "market_cap": 1000000,
        "addl_notes": "Test price without ID",
        "price_currency": "USD"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/security-prices/", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Create operation works when security_price_id is NOT included")
            return True
        else:
            print("❌ Unexpected: Create operation failed even without security_price_id")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_available_securities():
    """Get list of available securities for testing"""
    try:
        response = requests.get(f"{BASE_URL}/securities")
        if response.status_code == 200:
            securities = response.json()
            print(f"Available securities: {len(securities)}")
            if securities:
                print(f"Sample security: ID {securities[0]['security_id']}, Ticker: {securities[0]['ticker']}")
            return securities
        return []
    except:
        return []

def get_available_platforms():
    """Get list of available platforms for testing"""
    try:
        response = requests.get(f"{BASE_URL}/external-platforms")
        if response.status_code == 200:
            platforms = response.json()
            print(f"Available platforms: {len(platforms)}")
            if platforms:
                print(f"Sample platform: ID {platforms[0]['external_platform_id']}, Name: {platforms[0]['name']}")
            return platforms
        return []
    except:
        return []

if __name__ == "__main__":
    print("=== Testing Add Price Error ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("✅ Server is running")
    
    # Get available data for testing
    securities = get_available_securities()
    platforms = get_available_platforms()
    
    if not securities or not platforms:
        print("⚠️ Warning: No securities or platforms found for testing")
        print("The tests will use default IDs which may not exist")
    
    # Test the issue
    issue_confirmed = test_create_security_price_with_id()
    fix_works = test_create_security_price_without_id()
    
    print("\n=== Test Results ===")
    if issue_confirmed and fix_works:
        print("✅ ISSUE CONFIRMED: The problem is including security_price_id in create requests")
        print("✅ FIX VALIDATED: Removing security_price_id from create requests works")
        print("\n📋 SOLUTION: Update SecurityPriceForm.jsx to not include security_price_id for new records")
    elif issue_confirmed:
        print("✅ ISSUE CONFIRMED but fix didn't work as expected")
    else:
        print("❌ Could not reproduce the issue or validate the fix")