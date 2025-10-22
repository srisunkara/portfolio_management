#!/usr/bin/env python3
"""
Test script to analyze the security prices performance issue
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except:
        return False

def test_api_performance():
    """Test the performance of different API calls"""
    print("Testing security prices API performance...\n")
    
    # Test 1: No parameters (should trigger list_all - the slow one)
    print("1. Testing with NO parameters (list_all):")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/security-prices")
        end_time = time.time()
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {end_time - start_time:.2f} seconds")
        if response.status_code == 200:
            data = response.json()
            print(f"   Records returned: {len(data)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: With date range (should be faster)
    print("\n2. Testing with DATE RANGE (filtered):")
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    start_time = time.time()
    try:
        params = {'from_date': week_ago, 'to_date': today}
        response = requests.get(f"{BASE_URL}/security-prices", params=params)
        end_time = time.time()
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {end_time - start_time:.2f} seconds")
        if response.status_code == 200:
            data = response.json()
            print(f"   Records returned: {len(data)}")
            print(f"   Date range: {week_ago} to {today}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: With specific date (should be fastest)
    print("\n3. Testing with SPECIFIC DATE:")
    start_time = time.time()
    try:
        params = {'date': today}
        response = requests.get(f"{BASE_URL}/security-prices", params=params)
        end_time = time.time()
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {end_time - start_time:.2f} seconds")
        if response.status_code == 200:
            data = response.json()
            print(f"   Records returned: {len(data)}")
            print(f"   Date: {today}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

def analyze_frontend_call():
    """Analyze what the frontend is actually sending"""
    print("\n=== Frontend Analysis ===")
    print("The frontend SecurityPricesList.jsx component:")
    print("- Sets fromDate to last weekday")
    print("- Sets toDate to today") 
    print("- Sets ticker to empty string initially")
    print("- Calls: api.listSecurityPricesWithFilters(fromDate, toDate, ticker)")
    
    print("\nThis should call the API with from_date and to_date parameters,")
    print("which should trigger the filtered query, NOT list_all().")
    print("\nIf it's still slow, there might be:")
    print("1. An issue with parameter passing")
    print("2. Missing database indexes")
    print("3. A large dataset even with filtering")

if __name__ == "__main__":
    print("=== Security Prices Performance Analysis ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("✅ Server is running")
    
    test_api_performance()
    analyze_frontend_call()
    
    print("\n=== Performance Issue Analysis ===")
    print("Based on the code review:")
    print("✅ Frontend provides date filters by default") 
    print("✅ API has proper filtering logic")
    print("❓ Need to verify why it might still be calling list_all()")
    print("❓ Need to check if database indexes exist")