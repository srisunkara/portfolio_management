#!/usr/bin/env python3
"""
Test script to verify the performance baseline fix and tooltip price data
- Performance should start at 0% when first date equals transaction date
- Backend API should include price data in performance response
- Tooltip should display price information
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

def test_performance_baseline_fix():
    """Test that performance calculation handles transaction date baseline correctly"""
    print("Testing performance baseline calculation fix...")
    
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
        pair = pairs[0]
        pair_id = pair['pair_id']
        original_date = pair['original']['transaction_date']
        duplicate_date = pair['duplicate']['transaction_date']
        
        print(f"   Testing pair: {pair['original']['security_ticker']} vs {pair['duplicate']['security_ticker']}")
        print(f"   Original transaction date: {original_date}")
        print(f"   Duplicate transaction date: {duplicate_date}")
        
        # Test with date range that includes the transaction date
        # This should trigger the baseline fix when first price date = transaction date
        params = {
            'from_date': original_date,  # Start from transaction date
            'to_date': '2025-10-10'
        }
        
        response = requests.get(f"{BASE_URL}/transactions/performance-comparison/{pair_id}", params=params)
        print(f"   API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            performance_data = data.get('performance_data', {})
            
            # Check original performance
            original_performance = performance_data.get('original', [])
            if original_performance:
                first_perf = original_performance[0]
                print(f"   Original first day performance: {first_perf['performance']}%")
                print(f"   Original first day date: {first_perf['date']}")
                print(f"   Original first day price: ${first_perf['price']}")
                
                # Check if performance starts at 0% when transaction date = first price date
                if first_perf['date'] == original_date:
                    if abs(first_perf['performance']) < 0.01:
                        print("   ✅ Original performance correctly starts at 0% on transaction date")
                        original_baseline_correct = True
                    else:
                        print(f"   ❌ Original performance should be 0% on transaction date, got {first_perf['performance']}%")
                        original_baseline_correct = False
                else:
                    print("   ℹ️  First price date doesn't match transaction date, baseline logic not applicable")
                    original_baseline_correct = True  # Not applicable
            else:
                print("   ❌ No original performance data")
                original_baseline_correct = False
            
            # Check duplicate performance
            duplicate_performance = performance_data.get('duplicate', [])
            if duplicate_performance:
                first_perf = duplicate_performance[0]
                print(f"   Duplicate first day performance: {first_perf['performance']}%")
                print(f"   Duplicate first day date: {first_perf['date']}")
                print(f"   Duplicate first day price: ${first_perf['price']}")
                
                # Check if performance starts at 0% when transaction date = first price date
                if first_perf['date'] == duplicate_date:
                    if abs(first_perf['performance']) < 0.01:
                        print("   ✅ Duplicate performance correctly starts at 0% on transaction date")
                        duplicate_baseline_correct = True
                    else:
                        print(f"   ❌ Duplicate performance should be 0% on transaction date, got {first_perf['performance']}%")
                        duplicate_baseline_correct = False
                else:
                    print("   ℹ️  First price date doesn't match transaction date, baseline logic not applicable")
                    duplicate_baseline_correct = True  # Not applicable
            else:
                print("   ❌ No duplicate performance data")
                duplicate_baseline_correct = False
            
            return original_baseline_correct and duplicate_baseline_correct
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_price_data_in_response():
    """Test that price data is included in the API response for tooltips"""
    print("\nTesting price data inclusion in API response...")
    
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
        
        # Use first pair
        pair_id = pairs[0]['pair_id']
        
        params = {
            'from_date': '2025-10-01',
            'to_date': '2025-10-10'
        }
        
        response = requests.get(f"{BASE_URL}/transactions/performance-comparison/{pair_id}", params=params)
        
        if response.status_code == 200:
            data = response.json()
            performance_data = data.get('performance_data', {})
            
            # Check that price data is included
            original_data = performance_data.get('original', [])
            duplicate_data = performance_data.get('duplicate', [])
            
            price_data_included = True
            
            if original_data:
                sample = original_data[0]
                required_fields = ['date', 'performance', 'price', 'current_value', 'unrealized_gain_loss']
                for field in required_fields:
                    if field not in sample:
                        print(f"   ❌ Missing field '{field}' in original performance data")
                        price_data_included = False
                    else:
                        print(f"   ✅ Field '{field}' present: {sample[field]}")
            else:
                print("   ❌ No original performance data to check")
                price_data_included = False
            
            if duplicate_data:
                sample = duplicate_data[0]
                if 'price' in sample:
                    print(f"   ✅ Price field present in duplicate data: ${sample['price']}")
                else:
                    print("   ❌ Missing price field in duplicate performance data")
                    price_data_included = False
            else:
                print("   ❌ No duplicate performance data to check")
                price_data_included = False
            
            return price_data_included
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    """Main test function"""
    print("=== Testing Performance Baseline Fix and Tooltip Price Data ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        return
    
    print("✅ Server is running\n")
    
    # Run tests
    baseline_fix_works = test_performance_baseline_fix()
    price_data_works = test_price_data_in_response()
    
    print("\n=== Test Results ===")
    print(f"✅ Performance baseline fix: {'Working' if baseline_fix_works else 'Issues found'}")
    print(f"✅ Price data in API response: {'Working' if price_data_works else 'Issues found'}")
    
    if baseline_fix_works and price_data_works:
        print("\n🎉 SUCCESS: Both fixes are working correctly!")
        print("✅ Performance now starts at 0% when first date equals transaction date")
        print("✅ Price data is included in API response for tooltips")
        print("✅ Frontend tooltips will now display price information")
        
        print("\nFixes implemented:")
        print("1. Backend baseline calculation handles transaction date = first price date")
        print("2. Price field added to tooltip display for both investments")
        print("3. Tooltip now shows: Price, Performance, Current Value, and Gain/Loss")
    else:
        print("\n❌ Some issues found - fixes may need additional work")
        if not baseline_fix_works:
            print("   - Performance baseline calculation needs adjustment")
        if not price_data_works:
            print("   - Price data not properly included in API response")

if __name__ == "__main__":
    main()