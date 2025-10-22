#!/usr/bin/env python3
"""
Test script to reproduce the performance baseline issue where BA and VOO
show negative values (-4.26% and -10.40%) on the first date instead of 0.0%
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except:
        return False

def test_specific_performance_issue():
    """Test the specific BA vs VOO case mentioned in the issue"""
    print("Testing specific BA vs VOO performance issue...")
    print("Date range: 06/10/2025 to 10/10/2025")
    
    try:
        # First get linked pairs to find BA vs VOO pair
        pairs_response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        if pairs_response.status_code != 200:
            print(f"❌ Could not get linked pairs: {pairs_response.status_code}")
            return False
            
        pairs_data = pairs_response.json()
        pairs = pairs_data.get('pairs', [])
        
        print(f"Found {len(pairs)} linked pairs")
        
        # Look for BA vs VOO pair
        ba_voo_pair = None
        for pair in pairs:
            orig_ticker = pair['original']['security_ticker']
            dup_ticker = pair['duplicate']['security_ticker']
            if (orig_ticker == 'BA' and dup_ticker == 'VOO') or (orig_ticker == 'VOO' and dup_ticker == 'BA'):
                ba_voo_pair = pair
                break
        
        if not ba_voo_pair:
            print("❌ Could not find BA vs VOO pair")
            print("Available pairs:")
            for pair in pairs:
                print(f"  - {pair['original']['security_ticker']} vs {pair['duplicate']['security_ticker']}")
            return False
            
        print(f"✓ Found BA vs VOO pair: {ba_voo_pair['pair_id']}")
        
        # Test performance with the specific date range
        params = {
            'from_date': '2025-06-10',
            'to_date': '2025-10-10'
        }
        
        perf_response = requests.get(
            f"{BASE_URL}/transactions/performance-comparison/{ba_voo_pair['pair_id']}", 
            params=params
        )
        
        if perf_response.status_code != 200:
            print(f"❌ Performance API failed: {perf_response.status_code}")
            print(f"Error: {perf_response.text}")
            return False
            
        perf_data = perf_response.json()
        
        # Check the performance data for the first date
        original_data = perf_data['performance_data']['original']
        duplicate_data = perf_data['performance_data']['duplicate']
        
        if original_data:
            first_original = original_data[0]
            print(f"First date original ({perf_data['pair_info']['original']['security_ticker']}): {first_original['date']} = {first_original['performance']}%")
            
        if duplicate_data:
            first_duplicate = duplicate_data[0]
            print(f"First date duplicate ({perf_data['pair_info']['duplicate']['security_ticker']}): {first_duplicate['date']} = {first_duplicate['performance']}%")
            
        # Show the issue
        if original_data and duplicate_data:
            orig_first_perf = original_data[0]['performance']
            dup_first_perf = duplicate_data[0]['performance']
            
            print(f"\n🔍 ISSUE ANALYSIS:")
            print(f"Expected: Both should be 0.0% on first date")
            print(f"Actual: {perf_data['pair_info']['original']['security_ticker']} = {orig_first_perf}%, {perf_data['pair_info']['duplicate']['security_ticker']} = {dup_first_perf}%")
            
            if orig_first_perf == 0.0 and dup_first_perf == 0.0:
                print("✅ Issue is fixed - both start at 0.0%")
                return True
            else:
                print("❌ Issue still exists - values are not 0.0% on first date")
                
                # Debug the baseline calculation
                print(f"\nDEBUG INFO:")
                print(f"Original baseline price: ${perf_data['pair_info']['original']['initial_price']}")
                print(f"Duplicate baseline price: ${perf_data['pair_info']['duplicate']['initial_price']}")
                print(f"Original first actual price: ${original_data[0]['price']}")
                print(f"Duplicate first actual price: ${duplicate_data[0]['price']}")
                
                # Check if baseline equals first price
                orig_baseline = perf_data['pair_info']['original']['initial_price']
                orig_first_price = original_data[0]['price']
                dup_baseline = perf_data['pair_info']['duplicate']['initial_price']
                dup_first_price = duplicate_data[0]['price']
                
                print(f"\nBaseline vs First Price Check:")
                print(f"Original: baseline={orig_baseline}, first_price={orig_first_price}, equal={orig_baseline == orig_first_price}")
                print(f"Duplicate: baseline={dup_baseline}, first_price={dup_first_price}, equal={dup_baseline == dup_first_price}")
                
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Performance Baseline Issue ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("Server is running. Testing specific performance issue...")
    
    if test_specific_performance_issue():
        print("\n✅ Issue appears to be resolved")
    else:
        print("\n❌ Issue still exists - needs to be fixed")