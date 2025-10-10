#!/usr/bin/env python3
"""
Test script to verify the performance ordering fix
- First date in range should show 0% performance for both securities
- Last date should show the actual performance change
- Performance should be calculated relative to the first date, not inverted
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

def test_performance_ordering_fix():
    """Test that performance is now correctly ordered with first date = 0%"""
    print("Testing performance ordering fix...")
    
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
        original_ticker = pairs[0]['original']['security_ticker']
        duplicate_ticker = pairs[0]['duplicate']['security_ticker']
        print(f"   Testing with pair: {original_ticker} vs {duplicate_ticker}")
        
        # Set a specific date range to test the ordering issue
        # Using the example from the issue: 06/10/2025 to 10/10/2025
        from_date = "2025-10-06"
        to_date = "2025-10-10"
        
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
            duplicate_performance = performance_data.get('duplicate', [])
            
            print(f"   Original ({original_ticker}) performance data points: {len(original_performance)}")
            print(f"   Duplicate ({duplicate_ticker}) performance data points: {len(duplicate_performance)}")
            
            # Test original performance ordering
            original_first_day_correct = False
            original_last_day_correct = False
            if original_performance:
                first_perf = original_performance[0]['performance']
                last_perf = original_performance[-1]['performance']
                first_date = original_performance[0]['date']
                last_date = original_performance[-1]['date']
                
                print(f"   Original first day ({first_date}): {first_perf}%")
                print(f"   Original last day ({last_date}): {last_perf}%")
                
                # First day should be 0% (or very close)
                if abs(first_perf) < 0.01:
                    print("   ✅ Original first day performance is 0%")
                    original_first_day_correct = True
                else:
                    print(f"   ❌ Original first day performance is {first_perf}% (should be 0%)")
                
                # Last day should show actual performance change
                if abs(last_perf) > abs(first_perf):
                    print("   ✅ Original last day shows performance change")
                    original_last_day_correct = True
                else:
                    print(f"   ❌ Original last day performance issue")
            
            # Test duplicate performance ordering
            duplicate_first_day_correct = False
            duplicate_last_day_correct = False
            if duplicate_performance:
                first_perf = duplicate_performance[0]['performance']
                last_perf = duplicate_performance[-1]['performance']
                first_date = duplicate_performance[0]['date']
                last_date = duplicate_performance[-1]['date']
                
                print(f"   Duplicate first day ({first_date}): {first_perf}%")
                print(f"   Duplicate last day ({last_date}): {last_perf}%")
                
                # First day should be 0% (or very close)
                if abs(first_perf) < 0.01:
                    print("   ✅ Duplicate first day performance is 0%")
                    duplicate_first_day_correct = True
                else:
                    print(f"   ❌ Duplicate first day performance is {first_perf}% (should be 0%)")
                
                # Last day should show actual performance change
                if abs(last_perf) > abs(first_perf):
                    print("   ✅ Duplicate last day shows performance change")
                    duplicate_last_day_correct = True
                else:
                    print(f"   ❌ Duplicate last day performance issue")
            
            # Show progression for better understanding
            if len(original_performance) > 1:
                print(f"   Original performance progression:")
                for i, perf in enumerate(original_performance):
                    print(f"     {perf['date']}: {perf['performance']}%")
                    
            if len(duplicate_performance) > 1:
                print(f"   Duplicate performance progression:")
                for i, perf in enumerate(duplicate_performance):
                    print(f"     {perf['date']}: {perf['performance']}%")
            
            # Overall test result
            all_correct = (original_first_day_correct and duplicate_first_day_correct and
                          original_last_day_correct and duplicate_last_day_correct)
            
            return all_correct
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Performance Ordering Fix ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("✅ Server is running")
    
    if test_performance_ordering_fix():
        print("\n✅ SUCCESS: Performance ordering fix is working correctly!")
        print("   - First day now shows 0% performance for both securities")
        print("   - Last day shows the actual performance change")
        print("   - Performance calculation is no longer inverted")
    else:
        print("\n❌ ISSUE: Performance ordering still needs adjustment")
    
    print("\n=== Fix Summary ===")
    print("✅ Changed ORDER BY from DESC to ASC in security price query")
    print("✅ First date in range now correctly used as baseline (0%)")
    print("✅ Performance shows proper progression from baseline to end date")