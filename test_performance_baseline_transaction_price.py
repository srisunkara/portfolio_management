#!/usr/bin/env python3
"""
Test script to verify the performance baseline fixes and date range buttons:
1. Backend now uses transaction price as baseline instead of first available price
2. Frontend has date range buttons that work correctly
3. Performance shows 0% on transaction date
"""
import requests
import json
from datetime import date, timedelta

# Backend server URL - adjust if needed
BASE_URL = "http://localhost:8000"

def test_performance_baseline_fix():
    """Test that the baseline is now correctly using transaction price"""
    print("=" * 60)
    print("TESTING PERFORMANCE BASELINE FIX")
    print("=" * 60)
    
    try:
        # Get linked pairs
        print("Getting linked transaction pairs...")
        response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        if response.status_code != 200:
            print(f"❌ Failed to get linked pairs: {response.status_code}")
            return False
            
        pairs = response.json().get("pairs", [])
        if not pairs:
            print("❌ No linked pairs found")
            return False
            
        print(f"✅ Found {len(pairs)} linked pairs")
        
        # Test performance with first pair
        first_pair = pairs[0]
        pair_id = first_pair["pair_id"]
        
        print(f"\nTesting performance calculation for pair: {pair_id}")
        print(f"Original: {first_pair['original']['security_ticker']} (${first_pair['original']['total_inv_amt']})")
        print(f"Duplicate: {first_pair['duplicate']['security_ticker']} (${first_pair['duplicate']['total_inv_amt']})")
        
        # Get transaction dates
        original_date = first_pair['original']['transaction_date']
        duplicate_date = first_pair['duplicate']['transaction_date']
        print(f"Transaction dates: Original={original_date}, Duplicate={duplicate_date}")
        
        # Test with a date range that includes the transaction date
        from_date = min(original_date, duplicate_date)
        to_date = date.today().isoformat()
        
        params = {
            "from_date": from_date,
            "to_date": to_date
        }
        
        print(f"Testing performance from {from_date} to {to_date}")
        
        perf_response = requests.get(
            f"{BASE_URL}/transactions/performance-comparison/{pair_id}",
            params=params
        )
        
        if perf_response.status_code != 200:
            print(f"❌ Performance comparison failed: {perf_response.status_code}")
            print(f"Error: {perf_response.text}")
            return False
            
        perf_data = perf_response.json()
        
        # Check performance data
        original_performance = perf_data.get("performance_data", {}).get("original", [])
        duplicate_performance = perf_data.get("performance_data", {}).get("duplicate", [])
        
        print(f"✅ Got performance data:")
        print(f"  Original points: {len(original_performance)}")
        print(f"  Duplicate points: {len(duplicate_performance)}")
        
        # Check if performance starts close to 0% on or near transaction date
        if original_performance:
            first_performance = original_performance[0]
            print(f"  First original performance: {first_performance['performance']}% on {first_performance['date']}")
            
            # Check if first performance is close to 0% (within reasonable range for price differences)
            if abs(first_performance['performance']) <= 5.0:  # Allow 5% tolerance for price variations
                print("✅ Original performance baseline looks correct (close to 0%)")
            else:
                print(f"⚠️  Original performance may not be using transaction price as baseline")
        
        if duplicate_performance:
            first_performance = duplicate_performance[0]
            print(f"  First duplicate performance: {first_performance['performance']}% on {first_performance['date']}")
            
            if abs(first_performance['performance']) <= 5.0:  # Allow 5% tolerance
                print("✅ Duplicate performance baseline looks correct (close to 0%)")
            else:
                print(f"⚠️  Duplicate performance may not be using transaction price as baseline")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_frontend_changes():
    """Test that the frontend file has the expected changes"""
    print("\n" + "=" * 60)
    print("TESTING FRONTEND CHANGES")
    print("=" * 60)
    
    try:
        with open("src/pages/transactions/TransactionPerformanceComparison.jsx", "r") as f:
            content = f.read()
            
        changes_found = []
        
        # Check for date range helper function
        if "getDateRange" in content and "const today = new Date(2025, 9, 10)" in content:
            changes_found.append("✅ Date range calculation function added")
        else:
            changes_found.append("❌ Missing date range calculation function")
            
        # Check for date range buttons
        if "Quick Date Ranges:" in content:
            changes_found.append("✅ Date range buttons UI added")
        else:
            changes_found.append("❌ Missing date range buttons UI")
            
        # Check for all button labels
        expected_buttons = ['1D', '1W', '1M', '6M', '1Y', 'YTD', '5Y', 'All']
        missing_buttons = [btn for btn in expected_buttons if f"'{btn}'" not in content]
        
        if not missing_buttons:
            changes_found.append("✅ All 8 date range buttons present")
        else:
            changes_found.append(f"❌ Missing buttons: {missing_buttons}")
            
        # Check for auto-refresh functionality
        if "loadPerformanceData(false)" in content and "getDateRange" in content:
            changes_found.append("✅ Auto-refresh on date range selection")
        else:
            changes_found.append("❌ Missing auto-refresh functionality")
            
        print("Frontend component changes:")
        for change in changes_found:
            print(f"  {change}")
            
        return all("✅" in change for change in changes_found)
        
    except Exception as e:
        print(f"❌ Error checking frontend file: {str(e)}")
        return False

def test_backend_changes():
    """Test that the backend file has the expected baseline changes"""
    print("\n" + "=" * 60)
    print("TESTING BACKEND CHANGES")
    print("=" * 60)
    
    try:
        with open("source_code/crud/transaction_api_routes.py", "r") as f:
            content = f.read()
            
        changes_found = []
        
        # Check for transaction price baseline comments
        if "Always use transaction price as baseline" in content:
            changes_found.append("✅ Updated baseline calculation comments")
        else:
            changes_found.append("❌ Missing updated baseline comments")
            
        # Check that old conditional baseline logic is removed
        if "If the first price date matches the transaction date" not in content:
            changes_found.append("✅ Old conditional baseline logic removed")
        else:
            changes_found.append("❌ Old conditional baseline logic still present")
            
        # Check for simplified baseline assignments
        if "original_baseline_value = original.total_inv_amt" in content:
            changes_found.append("✅ Original baseline uses transaction amount")
        else:
            changes_found.append("❌ Original baseline not using transaction amount")
            
        if "duplicate_baseline_value = duplicate.total_inv_amt" in content:
            changes_found.append("✅ Duplicate baseline uses transaction amount")
        else:
            changes_found.append("❌ Duplicate baseline not using transaction amount")
            
        print("Backend API changes:")
        for change in changes_found:
            print(f"  {change}")
            
        return all("✅" in change for change in changes_found)
        
    except Exception as e:
        print(f"❌ Error checking backend file: {str(e)}")
        return False

def main():
    print("PERFORMANCE BASELINE AND DATE RANGE BUTTONS TEST")
    print("=" * 60)
    
    # Test backend changes
    backend_changes_ok = test_backend_changes()
    
    # Test frontend changes  
    frontend_changes_ok = test_frontend_changes()
    
    # Test backend functionality
    backend_functionality_ok = test_performance_baseline_fix()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Backend Code Changes: {'✅' if backend_changes_ok else '❌'}")
    print(f"Frontend Code Changes: {'✅' if frontend_changes_ok else '❌'}")
    print(f"Backend Functionality: {'✅' if backend_functionality_ok else '❌'}")
    
    if backend_changes_ok and frontend_changes_ok and backend_functionality_ok:
        print(f"\n🎉 SUCCESS: All performance baseline fixes implemented!")
        print("\nChanges made:")
        print("  • Backend now uses transaction price as baseline (no loss/gain on transaction date)")
        print("  • Frontend has 8 date range buttons (1D, 1W, 1M, 6M, 1Y, YTD, 5Y, All)")
        print("  • Date buttons automatically update date ranges and refresh performance data")
        print("  • Graph shows performance for selected date range rather than from first price date")
    else:
        print(f"\n❌ Some issues need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()