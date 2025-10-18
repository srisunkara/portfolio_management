#!/usr/bin/env python3
"""
Test script to verify the transaction performance page blank page fix
"""
import requests
import json
from datetime import date, timedelta

# Backend server URL
BASE_URL = "http://localhost:8000"

def test_backend_endpoints():
    """Test backend endpoints are working"""
    print("Testing backend endpoints...")
    
    try:
        # Test linked pairs
        response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        if response.status_code == 200:
            pairs = response.json().get("pairs", [])
            print(f"✅ Found {len(pairs)} linked transaction pairs")
            
            if pairs:
                # Test performance comparison
                pair_id = pairs[0]["pair_id"]
                to_date = date.today()
                from_date = to_date - timedelta(days=365)
                
                params = {
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat()
                }
                
                perf_response = requests.get(
                    f"{BASE_URL}/transactions/performance-comparison/{pair_id}",
                    params=params
                )
                
                if perf_response.status_code == 200:
                    data = perf_response.json()
                    original_points = len(data.get("performance_data", {}).get("original", []))
                    duplicate_points = len(data.get("performance_data", {}).get("duplicate", []))
                    print(f"✅ Performance data: {original_points} original, {duplicate_points} duplicate points")
                    return True, pairs[0]
                else:
                    print(f"❌ Performance endpoint failed: {perf_response.status_code}")
                    return False, None
            else:
                print("⚠️  No transaction pairs found")
                return True, None
        else:
            print(f"❌ Linked pairs endpoint failed: {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on port 8000?")
        return False, None
    except Exception as e:
        print(f"❌ Backend test error: {str(e)}")
        return False, None

def check_frontend_fix():
    """Check that the frontend fix is in place"""
    print("\nChecking frontend fix...")
    
    try:
        with open("src/pages/transactions/TransactionPerformanceComparison.jsx", "r") as f:
            content = f.read()
            
        # Check that allDates was replaced with allData
        if "allData.length" in content and "allDates" not in content:
            print("✅ Frontend fix applied: 'allDates' replaced with 'allData'")
            return True
        else:
            print("❌ Frontend fix not applied properly")
            return False
            
    except Exception as e:
        print(f"❌ Error checking frontend fix: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("TRANSACTION PERFORMANCE PAGE BLANK PAGE FIX TEST")
    print("=" * 60)
    
    # Test backend
    backend_ok, test_pair = test_backend_endpoints()
    
    # Check frontend fix
    frontend_ok = check_frontend_fix()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Backend Endpoints: {'✅' if backend_ok else '❌'}")
    print(f"Frontend Fix: {'✅' if frontend_ok else '❌'}")
    
    if backend_ok and frontend_ok:
        print(f"\n🎉 SUCCESS: Fix applied successfully!")
        print(f"📱 Test the page manually:")
        print(f"  1. Start frontend: npm run dev")
        print(f"  2. Navigate to: http://localhost:5173/transactions/performance-comparison")
        print(f"  3. Select a transaction pair and hit 'Refresh'")
        print(f"  4. Page should load chart without blank page error")
        
        if test_pair:
            print(f"\nTest data available:")
            print(f"  Pair: {test_pair['original']['security_ticker']} vs {test_pair['duplicate']['security_ticker']}")
    else:
        print(f"\n❌ Issues found that need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()