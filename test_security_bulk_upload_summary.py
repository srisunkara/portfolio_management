#!/usr/bin/env python3
"""
Test script to verify the security bulk upload summary format implementation
"""
import requests
import json
import tempfile
import os

# Backend server URL
BASE_URL = "http://localhost:8000"

def test_bulk_csv_string_endpoint():
    """Test the bulk-csv-string endpoint with summary format"""
    print("=" * 60)
    print("TESTING BULK CSV STRING ENDPOINT")
    print("=" * 60)
    
    try:
        # Test CSV data with mixed results
        csv_data = """ticker,name,company_name,security_currency,is_private
NEWTEST1,New Test 1,New Test Company 1,USD,false
AAPL,Apple Inc Updated,Apple Inc Updated,USD,false
NEWTEST2,New Test 2,New Test Company 2,USD,true
,Invalid Row,Missing Ticker,USD,false
NEWTEST1,Duplicate in Request,Duplicate Company,USD,false"""
        
        print("1. Testing bulk-csv-string with mixed data...")
        response = requests.post(
            f"{BASE_URL}/securities/bulk-csv-string",
            data=csv_data,
            headers={"Content-Type": "text/plain"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received successfully")
            
            # Check for new summary format
            if "added" in result and isinstance(result["added"], dict):
                print(f"✅ Added section: {result['added']['count']} tickers")
                print(f"   Tickers: {', '.join(result['added']['tickers'])}")
            else:
                print(f"❌ Missing added section with count and tickers")
                return False
                
            if "skipped" in result and isinstance(result["skipped"], dict):
                print(f"✅ Skipped section: {result['skipped']['count']} tickers")
                print(f"   Tickers: {', '.join(result['skipped']['tickers'])}")
            else:
                print(f"❌ Missing skipped section with count and tickers")
                return False
                
            if "failed" in result and isinstance(result["failed"], dict):
                print(f"✅ Failed section: {result['failed']['count']} tickers")
                print(f"   Tickers: {', '.join(result['failed']['tickers'])}")
            else:
                print(f"❌ Missing failed section with count and tickers")
                return False
                
            # Check for legacy counts (for backward compatibility)
            if "legacy_counts" in result:
                print(f"✅ Legacy counts included for backward compatibility")
            else:
                print(f"⚠️  No legacy counts (may break existing integrations)")
                
            return True
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_bulk_csv_file_endpoint():
    """Test the bulk-csv file upload endpoint with summary format"""
    print("\n" + "=" * 60)
    print("TESTING BULK CSV FILE ENDPOINT")
    print("=" * 60)
    
    try:
        # Create temporary CSV file
        csv_content = """ticker,name,company_name,security_currency,is_private
FILETEST1,File Test 1,File Test Company 1,USD,false
MSFT,Microsoft Updated,Microsoft Corporation Updated,USD,false
FILETEST2,File Test 2,File Test Company 2,EUR,true
INVALID,,Missing Name,USD,false
FILETEST1,Duplicate File,Duplicate File Company,USD,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
            
        try:
            print("1. Testing bulk-csv file upload with mixed data...")
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_securities.csv', f, 'text/csv')}
                response = requests.post(f"{BASE_URL}/securities/bulk-csv", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ File upload successful")
                
                # Check for new summary format
                if "added" in result and isinstance(result["added"], dict):
                    print(f"✅ Added section: {result['added']['count']} tickers")
                    print(f"   Tickers: {', '.join(result['added']['tickers'])}")
                else:
                    print(f"❌ Missing added section with count and tickers")
                    return False
                    
                if "skipped" in result and isinstance(result["skipped"], dict):
                    print(f"✅ Skipped section: {result['skipped']['count']} tickers")
                    print(f"   Tickers: {', '.join(result['skipped']['tickers'])}")
                else:
                    print(f"❌ Missing skipped section with count and tickers")
                    return False
                    
                if "failed" in result and isinstance(result["failed"], dict):
                    print(f"✅ Failed section: {result['failed']['count']} tickers")
                    print(f"   Tickers: {', '.join(result['failed']['tickers'])}")
                else:
                    print(f"❌ Missing failed section with count and tickers")
                    return False
                    
                # Check for legacy counts
                if "legacy_counts" in result:
                    print(f"✅ Legacy counts included for backward compatibility")
                else:
                    print(f"⚠️  No legacy counts (may break existing integrations)")
                    
                return True
            else:
                print(f"❌ File upload failed: {response.status_code} - {response.text}")
                return False
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_empty_requests():
    """Test edge cases with empty data"""
    print("\n" + "=" * 60)
    print("TESTING EMPTY DATA EDGE CASES")
    print("=" * 60)
    
    try:
        # Test empty CSV string
        print("1. Testing empty CSV string...")
        response = requests.post(
            f"{BASE_URL}/securities/bulk-csv-string",
            data="",
            headers={"Content-Type": "text/plain"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if (result.get("added", {}).get("count") == 0 and 
                result.get("skipped", {}).get("count") == 0 and 
                result.get("failed", {}).get("count") == 0):
                print("✅ Empty CSV string handled correctly")
            else:
                print("❌ Empty CSV string not handled correctly")
                return False
        else:
            print(f"❌ Empty CSV string test failed: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Empty data test error: {str(e)}")
        return False

def main():
    print("SECURITY BULK UPLOAD SUMMARY FORMAT TEST")
    print("=" * 60)
    print("Testing that security bulk upload endpoints return summary format")
    print("with counts and ticker lists like the download prices endpoint")
    print()
    
    # Test bulk-csv-string endpoint
    string_ok = test_bulk_csv_string_endpoint()
    
    # Test bulk-csv file endpoint
    file_ok = test_bulk_csv_file_endpoint()
    
    # Test empty data edge cases
    empty_ok = test_empty_requests()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Bulk CSV String: {'✅' if string_ok else '❌'}")
    print(f"Bulk CSV File: {'✅' if file_ok else '❌'}")
    print(f"Empty Data Cases: {'✅' if empty_ok else '❌'}")
    
    if string_ok and file_ok and empty_ok:
        print(f"\n🎉 SUCCESS: Security bulk upload summary format implemented!")
        print("\nNew response format:")
        print("  • added: {count, tickers} - securities created/updated")
        print("  • skipped: {count, tickers} - existing or invalid securities") 
        print("  • failed: {count, tickers} - securities that failed to process")
        print("  • legacy_counts: backward compatibility counters")
        print("\n📱 Both endpoints now match the download prices summary format")
    else:
        print(f"\n❌ Issues found that need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()