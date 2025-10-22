#!/usr/bin/env python3
"""
Test script to verify the SecurityPriceForm fix works correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

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

def get_test_data():
    """Get valid security and platform IDs for testing"""
    try:
        securities_response = requests.get(f"{BASE_URL}/securities")
        platforms_response = requests.get(f"{BASE_URL}/external-platforms")
        
        if securities_response.status_code == 200 and platforms_response.status_code == 200:
            securities = securities_response.json()
            platforms = platforms_response.json()
            
            if securities and platforms:
                return {
                    "security_id": securities[0]["security_id"],
                    "price_source_id": platforms[0]["external_platform_id"]
                }
    except:
        pass
    return None

def test_create_price_with_fixed_payload():
    """Test creating a security price with the corrected payload structure"""
    print("Testing create security price with fixed payload...")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    test_data = get_test_data()
    if not test_data:
        print("❌ Could not get valid test data")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # This mimics the fixed frontend payload - proper validation and no security_price_id for create
    payload = {
        "security_id": test_data["security_id"],
        "price_source_id": test_data["price_source_id"],
        "price_date": "2025-01-17",
        "price": 150.75,
        "market_cap": 5000000,
        "addl_notes": "Test price with fix",
        "price_currency": "USD"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/security-prices/", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Created price with ID {data.get('security_price_id')}")
            return data.get('security_price_id')
        else:
            print(f"❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_update_price_with_fixed_payload(price_id):
    """Test updating a security price with the corrected payload structure"""
    print(f"Testing update security price {price_id} with fixed payload...")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    test_data = get_test_data()
    if not test_data:
        print("❌ Could not get valid test data")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # This mimics the fixed frontend payload for update - includes security_price_id
    payload = {
        "security_price_id": price_id,
        "security_id": test_data["security_id"],
        "price_source_id": test_data["price_source_id"],
        "price_date": "2025-01-17",
        "price": 155.25,  # Updated price
        "market_cap": 5100000,  # Updated market cap
        "addl_notes": "Test price updated with fix",
        "price_currency": "USD"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/security-prices/{price_id}", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Updated price, new value: ${data.get('price')}")
            return True
        else:
            print(f"❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_create_price_validation():
    """Test that validation works for missing required fields"""
    print("Testing create security price validation (missing required fields)...")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test payload with missing required fields (this should fail)
    payload = {
        "security_id": None,  # Missing required field
        "price_source_id": None,  # Missing required field
        "price_date": "2025-01-18",
        "price": None,  # Missing required field
        "market_cap": 0,
        "addl_notes": None,
        "price_currency": "USD"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/security-prices/", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 422:  # Validation error
            print("✅ SUCCESS: Validation correctly rejected missing required fields")
            return True
        else:
            print(f"❌ UNEXPECTED: Should have failed validation but got: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Security Price Fix ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("✅ Server is running")
    
    # Test the fix
    created_price_id = test_create_price_with_fixed_payload()
    
    update_success = False
    if created_price_id:
        update_success = test_update_price_with_fixed_payload(created_price_id)
    
    validation_works = test_create_price_validation()
    
    print("\n=== Test Results ===")
    print(f"✅ Create operation: {'SUCCESS' if created_price_id else 'FAILED'}")
    print(f"✅ Update operation: {'SUCCESS' if update_success else 'FAILED'}")
    print(f"✅ Validation works: {'SUCCESS' if validation_works else 'FAILED'}")
    
    if created_price_id and update_success and validation_works:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The SecurityPriceForm fix is working correctly")
        print("✅ Create operations work without security_price_id")
        print("✅ Update operations work with security_price_id")
        print("✅ Validation prevents submission with missing required fields")
    else:
        print("\n❌ Some tests failed - the fix may need additional work")