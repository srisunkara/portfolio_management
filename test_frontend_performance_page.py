#!/usr/bin/env python3
"""
Test script to verify the frontend performance comparison page can load data
by testing both the linked-pairs endpoint and the performance-comparison endpoint
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

def test_linked_pairs_endpoint():
    """Test the linked-pairs endpoint that the frontend calls"""
    print("Testing /transactions/linked-pairs endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            print(f"Found {len(pairs)} transaction pairs")
            
            if pairs:
                print("Sample pairs:")
                for i, pair in enumerate(pairs[:2]):  # Show first 2 pairs
                    orig = pair["original"]
                    dup = pair["duplicate"]
                    print(f"  {i+1}. {orig['security_ticker']} vs {dup['security_ticker']} (${orig['total_inv_amt']})")
                return pairs
            else:
                print("No pairs found - this would show the 'No Linked Transaction Pairs Found' message")
                return []
        else:
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_performance_comparison_endpoint(pairs):
    """Test the performance comparison endpoint with actual pair data"""
    if not pairs:
        print("No pairs available to test performance comparison")
        return False
        
    print(f"\nTesting /transactions/performance-comparison endpoint...")
    
    # Use the first pair for testing
    pair = pairs[0]
    pair_id = pair["pair_id"]
    
    # Test with a 30-day date range
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        params = {
            'from_date': from_date,
            'to_date': to_date
        }
        
        url = f"{BASE_URL}/transactions/performance-comparison/{pair_id}"
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            pair_info = data.get("pair_info", {})
            performance_data = data.get("performance_data", {})
            
            orig_data = performance_data.get("original", [])
            dup_data = performance_data.get("duplicate", [])
            
            print(f"Performance data points:")
            print(f"  Original ({pair_info['original']['security_ticker']}): {len(orig_data)} data points")
            print(f"  Duplicate ({pair_info['duplicate']['security_ticker']}): {len(dup_data)} data points")
            
            if orig_data:
                print(f"  Sample original performance: {orig_data[0]['date']} -> {orig_data[0]['performance']}%")
            if dup_data:
                print(f"  Sample duplicate performance: {dup_data[0]['date']} -> {dup_data[0]['performance']}%")
                
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Frontend Performance Comparison Page Data ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("Server is running. Testing performance comparison endpoints...\n")
    
    # Test the linked-pairs endpoint (this is what was failing before)
    pairs = test_linked_pairs_endpoint()
    
    if pairs is None:
        print("❌ FAILED: linked-pairs endpoint is not working")
        exit(1)
    elif len(pairs) == 0:
        print("⚠️  WARNING: No transaction pairs found")
        print("   The page will show 'No Linked Transaction Pairs Found' message")
        print("   Create some duplicate transactions to see the performance comparison")
    else:
        print("✅ SUCCESS: linked-pairs endpoint working correctly")
        
        # Test the performance comparison endpoint
        if test_performance_comparison_endpoint(pairs):
            print("✅ SUCCESS: performance-comparison endpoint working correctly")
            print("\n🎉 RESULT: The frontend performance comparison page should now work!")
            print("   - Transaction pairs will load in the dropdown")
            print("   - Performance data will display when a pair and date range are selected")
        else:
            print("❌ FAILED: performance-comparison endpoint has issues")
    
    print(f"\nFrontend URL: http://localhost:5174/transactions/performance-comparison")