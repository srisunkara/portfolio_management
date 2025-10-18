#!/usr/bin/env python3
"""
Test script to reproduce the date range issue where the graph starts at 01/01/2024
instead of the selected date range 03/17/2020 to 10/10/2025
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

def test_date_range_issue():
    """Test the specific date range issue mentioned in the problem"""
    print("Testing date range issue...")
    print("Selected range: 03/17/2020 to 10/10/2025")
    print("Issue: Graph starts at 01/01/2024 instead")
    
    try:
        # Get linked pairs first
        pairs_response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        if pairs_response.status_code != 200:
            print("❌ Could not get linked pairs")
            return False
            
        pairs = pairs_response.json().get('pairs', [])
        if not pairs:
            print("❌ No linked pairs found")
            return False
            
        # Use the first pair for testing
        pair_id = pairs[0]['pair_id']
        print(f"Testing with pair: {pair_id}")
        
        # Test with the specific date range from the issue
        params = {
            'from_date': '2020-03-17',
            'to_date': '2025-10-10'
        }
        
        response = requests.get(f"{BASE_URL}/transactions/performance-comparison/{pair_id}", params=params)
        
        if response.status_code != 200:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
        data = response.json()
        performance_data = data.get('performance_data', {})
        
        # Check what date range the API actually returns
        original_data = performance_data.get('original', [])
        duplicate_data = performance_data.get('duplicate', [])
        
        all_dates = []
        if original_data:
            all_dates.extend([d['date'] for d in original_data])
        if duplicate_data:
            all_dates.extend([d['date'] for d in duplicate_data])
            
        if all_dates:
            min_date = min(all_dates)
            max_date = max(all_dates)
            
            print(f"\nAPI Results:")
            print(f"  Requested range: 2020-03-17 to 2025-10-10")
            print(f"  Actual data range: {min_date} to {max_date}")
            print(f"  Data points: {len(all_dates)} total")
            
            # Check if the issue exists
            if min_date.startswith('2024-01-01'):
                print("✅ ISSUE CONFIRMED: Data starts at 2024-01-01 instead of requested range")
                print("🔍 ROOT CAUSE: Frontend chart uses actual data dates for X-axis instead of selected range")
            elif min_date == '2020-03-17':
                print("✅ Data correctly starts from requested date")
            else:
                print(f"📊 Data starts from {min_date} (not 2024-01-01, but also not the requested start date)")
                
            print(f"\nFirst few data points:")
            for i, date in enumerate(sorted(set(all_dates))[:5]):
                print(f"  {i+1}. {date}")
                
            return True
        else:
            print("❌ No performance data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def analyze_issue():
    """Analyze the root cause and solution"""
    print("\n=== ISSUE ANALYSIS ===")
    print("🔍 ROOT CAUSE:")
    print("  The frontend chart calculates X-axis range from actual data:")
    print("  - Lines 267-269: const allDates = allData.map(d => new Date(d.date))")
    print("  - Lines 268-269: const minDate = new Date(Math.min(...allDates))")
    print("  - This means the chart only shows dates where data exists")
    
    print("\n💡 SOLUTION NEEDED:")
    print("  The chart should use the user-selected date range for X-axis:")
    print("  - Use fromDate and toDate props from the component state")
    print("  - Show the full selected range even if no data exists for some dates")
    print("  - This will give users the correct timeline perspective")
    
    return True

if __name__ == "__main__":
    print("=== Testing Date Range Issue ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("✅ Server is running\n")
    
    # Test the specific issue
    issue_reproduced = test_date_range_issue()
    analysis_complete = analyze_issue()
    
    print(f"\n=== RESULTS ===")
    if issue_reproduced:
        print("✅ Issue analysis complete")
        print("🎯 Next step: Fix the frontend chart to use selected date range for X-axis")
    else:
        print("❌ Could not reproduce the issue or analyze the data")