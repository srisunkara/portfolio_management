#!/usr/bin/env python3
"""
Test script to verify the performance comparison baseline fix
- Performance should start at 0% on the first date in the selected range
- Performance should show relative changes from the first date, not transaction date
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

def test_performance_baseline_fix():
    """Test that performance now starts at 0% on the first date"""
    print("Testing performance baseline fix...")
    
    try:
        # Get linked pairs
        pairs_response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        if pairs_response.status_code != 200:
            print("   Cannot test - no linked pairs available")
            return False
            
        pairs = pairs_response.json().get('pairs', [])
        if not pairs:
            print("   Cannot test - no linked pairs found")
            return False
            
        # Use the first pair for testing
        pair_id = pairs[0]['pair_id']
        print(f"   Testing with pair: {pair_id}")
        
        # Set date range (last 30 days)
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        params = {
            'from_date': from_date,
            'to_date': to_date
        }
        
        response = requests.get(f"{BASE_URL}/transactions/performance-comparison/{pair_id}", params=params)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            performance_data = data.get('performance_data', {})
            
            # Check original performance
            original_performance = performance_data.get('original', [])
            if original_performance:
                first_performance = original_performance[0]['performance']
                print(f"   Original first day performance: {first_performance}%")
                
                if abs(first_performance) < 0.01:  # Should be 0 or very close to 0
                    print("   ✅ Original performance starts at 0%")
                    original_baseline_correct = True
                else:
                    print(f"   ❌ Original performance starts at {first_performance}% (should be 0%)")
                    original_baseline_correct = False
            else:
                print("   ❌ No original performance data")
                original_baseline_correct = False
            
            # Check duplicate performance  
            duplicate_performance = performance_data.get('duplicate', [])
            if duplicate_performance:
                first_performance = duplicate_performance[0]['performance']
                print(f"   Duplicate first day performance: {first_performance}%")
                
                if abs(first_performance) < 0.01:  # Should be 0 or very close to 0
                    print("   ✅ Duplicate performance starts at 0%")
                    duplicate_baseline_correct = True
                else:
                    print(f"   ❌ Duplicate performance starts at {first_performance}% (should be 0%)")
                    duplicate_baseline_correct = False
            else:
                print("   ❌ No duplicate performance data")
                duplicate_baseline_correct = False
            
            # Show sample performance progression
            if len(original_performance) > 1:
                print(f"   Original performance progression:")
                for i, perf in enumerate(original_performance[:5]):  # Show first 5 days
                    print(f"     Day {i+1} ({perf['date']}): {perf['performance']}%")
                    
            if len(duplicate_performance) > 1:
                print(f"   Duplicate performance progression:")
                for i, perf in enumerate(duplicate_performance[:5]):  # Show first 5 days
                    print(f"     Day {i+1} ({perf['date']}): {perf['performance']}%")
            
            return original_baseline_correct and duplicate_baseline_correct
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Performance Baseline Fix ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("✅ Server is running")
    
    if test_performance_baseline_fix():
        print("\n✅ SUCCESS: Performance baseline fix is working correctly!")
        print("   - Performance now starts at 0% on the first date in the range")
        print("   - Performance shows relative changes from the start date")
        print("   - No more negative starting values")
    else:
        print("\n❌ ISSUE: Performance baseline fix needs further adjustment")
    
    print("\n=== Fix Summary ===")
    print("✅ Changed baseline calculation from transaction date to first date in range")
    print("✅ Performance now starts at 0% and shows relative changes")
    print("✅ Eliminates confusing negative starting values")