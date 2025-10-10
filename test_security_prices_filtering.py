#!/usr/bin/env python3
"""
Test script to verify the new security prices filtering functionality
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except:
        return False

def test_security_prices_filtering():
    """Test the new filtering parameters"""
    print("Testing security prices filtering...")
    
    # Test 1: No filters (should work like before)
    print("\n1. Testing no filters:")
    response = requests.get(f"{BASE_URL}/security-prices")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Records returned: {len(data)}")
    
    # Test 2: Date range filter
    print("\n2. Testing date range filter:")
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    params = {
        'from_date': week_ago,
        'to_date': today
    }
    response = requests.get(f"{BASE_URL}/security-prices", params=params)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Records returned: {len(data)}")
        print(f"   Date range: {week_ago} to {today}")
    
    # Test 3: Ticker filter
    print("\n3. Testing ticker filter:")
    params = {'ticker': 'VOO'}
    response = requests.get(f"{BASE_URL}/security-prices", params=params)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Records returned: {len(data)}")
        print(f"   Ticker filter: VOO")
    
    # Test 4: Combined filters
    print("\n4. Testing combined filters:")
    params = {
        'from_date': week_ago,
        'to_date': today,
        'ticker': 'VOO'
    }
    response = requests.get(f"{BASE_URL}/security-prices", params=params)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Records returned: {len(data)}")
        print(f"   Combined filters: {week_ago} to {today}, ticker=VOO")

def test_legacy_compatibility():
    """Test that legacy single date parameter still works"""
    print("\n5. Testing legacy date parameter compatibility:")
    today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(f"{BASE_URL}/security-prices?date={today}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Records returned: {len(data)}")
        print(f"   Legacy date filter: {today}")

if __name__ == "__main__":
    print("=== Testing Security Prices Filtering ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    try:
        test_security_prices_filtering()
        test_legacy_compatibility()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")