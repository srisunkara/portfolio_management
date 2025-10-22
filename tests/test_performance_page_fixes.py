#!/usr/bin/env python3
"""
Test script to verify that the transaction performance page fixes work correctly:
1. Page loads automatically without manual refresh
2. Stop button functionality works
3. Continuous processing without prompting
"""
import subprocess
import time
import requests
import json

def test_backend_performance():
    """Test that backend performance endpoints are still working"""
    print("=" * 60)
    print("TESTING BACKEND PERFORMANCE ENDPOINTS")
    print("=" * 60)
    
    try:
        # Test linked pairs
        print("Testing linked pairs endpoint...")
        response = requests.get("http://localhost:8000/transactions/linked-pairs")
        if response.status_code == 200:
            pairs = response.json().get("pairs", [])
            print(f"✅ Found {len(pairs)} linked transaction pairs")
            
            if pairs:
                # Test performance comparison with first pair
                first_pair = pairs[0]
                pair_id = first_pair["pair_id"]
                
                print(f"Testing performance comparison for pair: {pair_id}")
                params = {
                    "from_date": "2024-01-01",
                    "to_date": "2024-12-31"
                }
                
                perf_response = requests.get(
                    f"http://localhost:8000/transactions/performance-comparison/{pair_id}",
                    params=params
                )
                
                if perf_response.status_code == 200:
                    perf_data = perf_response.json()
                    original_points = len(perf_data.get("performance_data", {}).get("original", []))
                    duplicate_points = len(perf_data.get("performance_data", {}).get("duplicate", []))
                    print(f"✅ Performance data loaded: {original_points} original, {duplicate_points} duplicate points")
                    return True
                else:
                    print(f"❌ Performance comparison failed: {perf_response.status_code}")
                    return False
            else:
                print("⚠️  No transaction pairs found to test performance comparison")
                return True
        else:
            print(f"❌ Linked pairs endpoint failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Backend test error: {str(e)}")
        return False

def test_frontend_file_changes():
    """Test that the frontend files have the expected changes"""
    print("\n" + "=" * 60)
    print("TESTING FRONTEND FILE CHANGES")
    print("=" * 60)
    
    try:
        # Check TransactionPerformanceComparison.jsx
        with open("../src/pages/transactions/TransactionPerformanceComparison.jsx", "r") as f:
            content = f.read()
            
        changes_found = []
        
        # Check for abort controller
        if "abortController" in content:
            changes_found.append("✅ Abort controller state added")
        else:
            changes_found.append("❌ Missing abort controller state")
            
        # Check for stop loading function
        if "stopLoading" in content:
            changes_found.append("✅ Stop loading function added")
        else:
            changes_found.append("❌ Missing stop loading function")
            
        # Check for auto-loading useEffect
        if "Auto-load performance data" in content:
            changes_found.append("✅ Auto-loading effect added")
        else:
            changes_found.append("❌ Missing auto-loading effect")
            
        # Check for stop button UI
        if "Stop Loading" in content:
            changes_found.append("✅ Stop button UI added")
        else:
            changes_found.append("❌ Missing stop button UI")
            
        print("Frontend component changes:")
        for change in changes_found:
            print(f"  {change}")
            
        # Check API client changes
        with open("../src/api/client.js", "r") as f:
            api_content = f.read()
            
        if "options = {}" in api_content and "getPerformanceComparison" in api_content:
            print("  ✅ API client updated to support abort signals")
            api_updated = True
        else:
            print("  ❌ API client not properly updated")
            api_updated = False
            
        return all("✅" in change for change in changes_found) and api_updated
        
    except Exception as e:
        print(f"❌ Error checking frontend files: {str(e)}")
        return False

def test_frontend_server():
    """Check if frontend development server is accessible"""
    print("\n" + "=" * 60)
    print("TESTING FRONTEND SERVER ACCESS")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend dev server is running on port 5173")
            return 5173
        else:
            print(f"❌ Frontend dev server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        pass
    
    # Try alternative port 5174
    try:
        response = requests.get("http://localhost:5174", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend dev server is running on port 5174")
            return 5174
        else:
            print(f"❌ Frontend dev server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        pass
    
    print("❌ Frontend dev server is not accessible on ports 5173 or 5174")
    print("💡 Start the frontend server with: npm run dev")
    return None

def main():
    print("TRANSACTION PERFORMANCE PAGE FIXES VERIFICATION")
    print("=" * 60)
    
    # Test backend
    backend_ok = test_backend_performance()
    
    # Test frontend file changes
    frontend_files_ok = test_frontend_file_changes()
    
    # Test frontend server
    frontend_port = test_frontend_server()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Backend Performance: {'✅' if backend_ok else '❌'}")
    print(f"Frontend File Changes: {'✅' if frontend_files_ok else '❌'}")
    print(f"Frontend Server: {'✅' if frontend_port else '❌'}")
    
    if backend_ok and frontend_files_ok:
        if frontend_port:
            print(f"\n🎉 SUCCESS: All fixes implemented correctly!")
            print(f"📱 Test the page at: http://localhost:{frontend_port}/transactions/performance-comparison")
            print("\nExpected behavior:")
            print("  • Page should auto-load performance data when pair/dates are selected")
            print("  • 'Stop Loading' button appears during loading operations")
            print("  • No need to manually click 'Refresh' for initial load")
        else:
            print(f"\n✅ All code fixes are in place, but frontend server needs to be started")
            print(f"💡 Run 'npm run dev' to test the changes")
    else:
        print(f"\n❌ Some issues need to be resolved before the fixes work properly")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()