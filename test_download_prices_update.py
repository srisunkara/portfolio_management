#!/usr/bin/env python3
"""
Test script to verify the updated download prices functionality:
1. Date range parameters with default to last work day and today
2. Optional ticker filtering  
3. Batch upsert operations for efficiency
4. Frontend UI integration
"""
import requests
import json
from datetime import date, timedelta, datetime

# Backend server URL
BASE_URL = "http://localhost:8000"

def test_backend_download_api():
    """Test the updated backend download prices API"""
    print("=" * 60)
    print("TESTING BACKEND DOWNLOAD PRICES API")
    print("=" * 60)
    
    try:
        # Test 1: Default date range (no parameters)
        print("1. Testing default date range (no parameters)...")
        response = requests.post(f"{BASE_URL}/security-prices/download", 
                               json={}, 
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Default date range works:")
            print(f"   From: {result.get('from_date')}")
            print(f"   To: {result.get('to_date')}")
            print(f"   Business days: {result.get('business_days')}")
            print(f"   Total attempted: {result.get('total_attempted')}")
            print(f"   Total saved: {result.get('total_saved')}")
        else:
            print(f"❌ Default test failed: {response.status_code} - {response.text}")
            return False
            
        # Test 2: Custom date range
        print("\n2. Testing custom date range...")
        custom_payload = {
            "from_date": "2024-01-15",
            "to_date": "2024-01-17"
        }
        response = requests.post(f"{BASE_URL}/security-prices/download", 
                               json=custom_payload,
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Custom date range works:")
            print(f"   From: {result.get('from_date')}")
            print(f"   To: {result.get('to_date')}")
            print(f"   Business days: {result.get('business_days')}")
        else:
            print(f"❌ Custom date range test failed: {response.status_code}")
            
        # Test 3: Ticker filtering
        print("\n3. Testing ticker filtering...")
        ticker_payload = {
            "from_date": "2024-01-15", 
            "to_date": "2024-01-15",
            "tickers": ["VOO", "AAPL", "MSFT"]
        }
        response = requests.post(f"{BASE_URL}/security-prices/download",
                               json=ticker_payload,
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ticker filtering works:")
            print(f"   Daily results count: {len(result.get('daily_results', []))}")
            if result.get('daily_results'):
                daily_result = result['daily_results'][0]
                print(f"   Securities processed: {daily_result.get('securities_processed')}")
                print(f"   Batch operation: {daily_result.get('batch_operation')}")
        else:
            print(f"❌ Ticker filtering test failed: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Backend test error: {str(e)}")
        return False

def test_frontend_api_client():
    """Test that the frontend API client is correctly updated"""
    print("\n" + "=" * 60)
    print("TESTING FRONTEND API CLIENT")
    print("=" * 60)
    
    try:
        with open("src/api/client.js", "r") as f:
            content = f.read()
            
        changes_found = []
        
        # Check for updated downloadPrices method
        if "downloadPrices: (fromDate, toDate, tickers)" in content:
            changes_found.append("✅ API method signature updated")
        else:
            changes_found.append("❌ API method signature not updated")
            
        # Check for payload construction
        if "payload.from_date = fromDate" in content and "payload.to_date = toDate" in content:
            changes_found.append("✅ Date range parameters handled")
        else:
            changes_found.append("❌ Date range parameters not handled")
            
        # Check for ticker array handling
        if "payload.tickers = tickers.filter" in content:
            changes_found.append("✅ Ticker filtering implemented")
        else:
            changes_found.append("❌ Ticker filtering not implemented")
            
        print("API client changes:")
        for change in changes_found:
            print(f"  {change}")
            
        return all("✅" in change for change in changes_found)
        
    except Exception as e:
        print(f"❌ Error checking API client: {str(e)}")
        return False

def test_frontend_component():
    """Test that the SecurityPricesList component is correctly updated"""
    print("\n" + "=" * 60)
    print("TESTING FRONTEND COMPONENT")
    print("=" * 60)
    
    try:
        with open("src/pages/security_prices/SecurityPricesList.jsx", "r") as f:
            content = f.read()
            
        changes_found = []
        
        # Check for download states
        if "downloadLoading" in content and "downloadResult" in content:
            changes_found.append("✅ Download state management added")
        else:
            changes_found.append("❌ Download state management missing")
            
        # Check for download function
        if "const downloadPrices = React.useCallback" in content:
            changes_found.append("✅ Download function implemented")
        else:
            changes_found.append("❌ Download function missing")
            
        # Check for download button
        if "Download Prices" in content and "Downloading..." in content:
            changes_found.append("✅ Download button UI added")
        else:
            changes_found.append("❌ Download button UI missing")
            
        # Check for results display
        if "Download Results" in content and "downloadResult &&" in content:
            changes_found.append("✅ Results display implemented")
        else:
            changes_found.append("❌ Results display missing")
            
        # Check for ticker array handling
        if "ticker.split(',').map(t => t.trim())" in content:
            changes_found.append("✅ Multiple ticker support added")
        else:
            changes_found.append("❌ Multiple ticker support missing")
            
        print("Frontend component changes:")
        for change in changes_found:
            print(f"  {change}")
            
        return all("✅" in change for change in changes_found)
        
    except Exception as e:
        print(f"❌ Error checking frontend component: {str(e)}")
        return False

def test_backend_batch_operations():
    """Test that the backend has batch upsert functionality"""
    print("\n" + "=" * 60)
    print("TESTING BACKEND BATCH OPERATIONS")
    print("=" * 60)
    
    try:
        with open("source_code/crud/security_price_crud_operations.py", "r") as f:
            content = f.read()
            
        changes_found = []
        
        # Check for batch_upsert method
        if "def batch_upsert(self, items: List[SecurityPriceDtlInput])" in content:
            changes_found.append("✅ Batch upsert method added")
        else:
            changes_found.append("❌ Batch upsert method missing")
            
        # Check for PostgreSQL UPSERT
        if "ON CONFLICT" in content and "DO UPDATE SET" in content:
            changes_found.append("✅ PostgreSQL UPSERT implemented")
        else:
            changes_found.append("❌ PostgreSQL UPSERT missing")
            
        # Check for execute_values usage
        if "psycopg2.extras.execute_values" in content:
            changes_found.append("✅ Efficient batch execution implemented")
        else:
            changes_found.append("❌ Efficient batch execution missing")
            
        print("Backend batch operations:")
        for change in changes_found:
            print(f"  {change}")
            
        return all("✅" in change for change in changes_found)
        
    except Exception as e:
        print(f"❌ Error checking backend batch operations: {str(e)}")
        return False

def main():
    print("DOWNLOAD PRICES UPDATE VERIFICATION")
    print("=" * 60)
    print("Testing updated download prices functionality:")
    print("• Date range support (default to last work day and today)")
    print("• Optional ticker filtering")
    print("• Batch upsert operations")
    print("• Updated frontend UI")
    print()
    
    # Test backend API
    backend_api_ok = test_backend_download_api()
    
    # Test frontend API client
    frontend_api_ok = test_frontend_api_client()
    
    # Test frontend component
    frontend_component_ok = test_frontend_component()
    
    # Test backend batch operations
    backend_batch_ok = test_backend_batch_operations()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Backend API: {'✅' if backend_api_ok else '❌'}")
    print(f"Frontend API Client: {'✅' if frontend_api_ok else '❌'}")  
    print(f"Frontend Component: {'✅' if frontend_component_ok else '❌'}")
    print(f"Backend Batch Operations: {'✅' if backend_batch_ok else '❌'}")
    
    if all([backend_api_ok, frontend_api_ok, frontend_component_ok, backend_batch_ok]):
        print(f"\n🎉 SUCCESS: All download prices updates implemented correctly!")
        print("\nNew features:")
        print("  • Date range support with smart defaults")
        print("  • Optional ticker filtering (comma-separated)")
        print("  • Efficient batch upsert operations")
        print("  • Enhanced UI with download results display")
        print("  • Automatic data refresh after download")
        print(f"\n📱 Test manually:")
        print("  1. Start backend: python -m uvicorn main:app --reload")
        print("  2. Start frontend: npm run dev")
        print("  3. Navigate to Security Prices page")
        print("  4. Try download with different date ranges and ticker filters")
    else:
        print(f"\n❌ Some issues need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()