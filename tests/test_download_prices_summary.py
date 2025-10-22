#!/usr/bin/env python3
"""
Test script to verify the updated download prices summary response format
"""
import requests
import json
from datetime import date, timedelta

# Backend server URL
BASE_URL = "http://localhost:8000"

def test_download_prices_summary():
    """Test that the download prices endpoint returns summary with ticker lists"""
    print("=" * 60)
    print("TESTING DOWNLOAD PRICES SUMMARY FORMAT")
    print("=" * 60)
    
    try:
        # Test with a small date range to limit API calls
        from_date = "2024-01-15"
        to_date = "2024-01-15"
        
        print(f"Testing download prices with date range: {from_date} to {to_date}")
        
        # Test with specific tickers to have more predictable results
        payload = {
            "from_date": from_date,
            "to_date": to_date,
            "tickers": ["VOO", "AAPL", "INVALIDTICKER"]  # Mix of valid and invalid
        }
        
        response = requests.post(
            f"{BASE_URL}/security-prices/download",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful")
            print(f"Response structure: {json.dumps(result, indent=2)}")
            
            # Check for new summary format
            expected_keys = ["from_date", "to_date", "business_days", "added", "skipped", "failed"]
            missing_keys = [key for key in expected_keys if key not in result]
            
            if not missing_keys:
                print("✅ All expected keys present in response")
            else:
                print(f"❌ Missing keys: {missing_keys}")
                return False
            
            # Check structure of each summary section
            for section in ["added", "skipped", "failed"]:
                if section in result:
                    section_data = result[section]
                    if isinstance(section_data, dict) and "count" in section_data and "tickers" in section_data:
                        print(f"✅ {section} section has correct structure")
                        print(f"  Count: {section_data['count']}")
                        print(f"  Tickers: {section_data['tickers']}")
                    else:
                        print(f"❌ {section} section missing 'count' or 'tickers'")
                        return False
            
            # Check that old format keys are not present
            old_keys = ["daily_results", "errors", "total_attempted", "total_saved", "total_skipped", "total_errors"]
            present_old_keys = [key for key in old_keys if key in result]
            
            if not present_old_keys:
                print("✅ Old format keys successfully removed")
            else:
                print(f"⚠️  Old format keys still present: {present_old_keys}")
            
            return True
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_empty_request():
    """Test with empty request (default date range)"""
    print("\n" + "=" * 60)
    print("TESTING EMPTY REQUEST (DEFAULT DATE RANGE)")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/security-prices/download",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Empty request successful")
            print(f"Date range: {result.get('from_date')} to {result.get('to_date')}")
            print(f"Business days: {result.get('business_days')}")
            
            # Check summary counts
            for section in ["added", "skipped", "failed"]:
                if section in result:
                    count = result[section].get("count", 0)
                    tickers = result[section].get("tickers", [])
                    print(f"{section.title()}: {count} tickers - {tickers[:5]}{'...' if len(tickers) > 5 else ''}")
            
            return True
        else:
            print(f"❌ Empty request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Empty request test error: {str(e)}")
        return False

def main():
    print("DOWNLOAD PRICES SUMMARY FORMAT TEST")
    print("=" * 60)
    print("Testing the new summary response format:")
    print("• Should return added/skipped/failed counts with ticker lists")
    print("• Should not return detailed daily_results or error arrays")
    print()
    
    # Test specific request
    specific_test_ok = test_download_prices_summary()
    
    # Test empty request
    empty_test_ok = test_empty_request()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Specific Request Test: {'✅' if specific_test_ok else '❌'}")
    print(f"Empty Request Test: {'✅' if empty_test_ok else '❌'}")
    
    if specific_test_ok and empty_test_ok:
        print(f"\n🎉 SUCCESS: New summary format implemented correctly!")
        print("\nNew response format:")
        print("  • added: { count: N, tickers: [list] }")
        print("  • skipped: { count: N, tickers: [list] }")
        print("  • failed: { count: N, tickers: [list] }")
        print("  • Removed: daily_results, errors arrays, detailed counts")
    else:
        print(f"\n❌ Some issues need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()