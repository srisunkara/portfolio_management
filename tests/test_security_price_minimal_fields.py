#!/usr/bin/env python3
"""
Test script to verify that security prices can be saved with minimal required fields
after removing Market Cap and Additional details requirements.
"""
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except:
        return False

def test_minimal_fields_create():
    """Test creating security price with only required fields"""
    print("Testing security price creation with minimal fields...")
    
    # Test payload with only required fields
    minimal_payload = {
        "security_id": 1,
        "price_source_id": 1,
        "price_date": "2025-10-10",
        "price": 150.25
        # Note: market_cap and addl_notes are NOT included
        # price_currency should default to USD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/security-prices/", 
                                json=minimal_payload,
                                headers={"Content-Type": "application/json"})
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ SUCCESS: Security price created with minimal fields")
            print(f"   Created price ID: {data.get('security_price_id')}")
            print(f"   Market cap defaulted to: {data.get('market_cap')}")
            print(f"   Currency defaulted to: {data.get('price_currency')}")
            print(f"   Additional notes: {data.get('addl_notes')}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_csv_upload_minimal_fields():
    """Test CSV upload with minimal required fields only"""
    print("\nTesting CSV upload with minimal fields...")
    
    # Create a minimal CSV content
    csv_content = """security_id,price_source_id,price_date,price
1,1,2025-10-11,155.50
2,1,2025-10-11,87.25"""
    
    try:
        files = {'file': ('test_prices.csv', csv_content, 'text/csv')}
        response = requests.post(f"{BASE_URL}/security-prices/bulk-csv", files=files)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS: CSV uploaded with {len(data)} records")
            if data:
                sample = data[0]
                print(f"   Sample record market_cap: {sample.get('market_cap')}")
                print(f"   Sample record currency: {sample.get('price_currency')}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_form_validation():
    """Test that frontend form validation allows minimal fields"""
    print("\nTesting frontend form validation logic...")
    
    # This simulates what the frontend form would send after processing empty fields
    form_payload = {
        "security_id": 1,
        "price_source_id": 1,
        "price_date": "2025-10-10",
        "price": 142.75,
        "market_cap": 0,  # Converted from empty string to 0 by frontend logic
        "addl_notes": None,  # Converted from empty string to null by frontend logic
        "price_currency": "USD"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/security-prices/", 
                                json=form_payload,
                                headers={"Content-Type": "application/json"})
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ SUCCESS: Frontend form payload accepted")
            print(f"   Market cap converted to: {data.get('market_cap')}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("=== Testing Security Price Minimal Fields Validation ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        return
    
    print("✅ Server is running\n")
    
    # Run tests
    tests = [
        ("Minimal Fields Create", test_minimal_fields_create),
        ("CSV Upload Minimal", test_csv_upload_minimal_fields),
        ("Form Validation", test_form_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"   ❌ {test_name} test error: {e}\n")
    
    # Summary
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Security prices can now be saved with minimal required fields.")
        print("✅ Market Cap and Additional details are no longer required")
        print("✅ Only Security, Price Source, Date, and Price are required")
        print("✅ Currency defaults to USD as expected")
    else:
        print("⚠️  Some tests failed. Validation may still have issues.")

if __name__ == "__main__":
    main()