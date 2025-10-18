#!/usr/bin/env python3
"""
Test script to reproduce transaction performance page loading issue
"""
import requests
import json
from datetime import date, timedelta

# Backend server URL - adjust if needed
BASE_URL = "http://localhost:8000"

def test_linked_pairs_endpoint():
    """Test the linked transaction pairs endpoint"""
    try:
        print("Testing /transactions/linked-pairs endpoint...")
        response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data.get("pairs", [])
        else:
            print(f"Error response: {response.text}")
            return []
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend server. Is it running on port 8000?")
        return []
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return []

def test_performance_comparison_endpoint(pair_id):
    """Test the performance comparison endpoint with a specific pair"""
    try:
        print(f"\nTesting /transactions/performance-comparison/{pair_id} endpoint...")
        
        # Use date range of last 30 days
        to_date = date.today()
        from_date = to_date - timedelta(days=30)
        
        params = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        }
        
        response = requests.get(
            f"{BASE_URL}/transactions/performance-comparison/{pair_id}",
            params=params
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Performance data loaded successfully")
            print(f"Original data points: {len(data.get('performance_data', {}).get('original', []))}")
            print(f"Duplicate data points: {len(data.get('performance_data', {}).get('duplicate', []))}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("TRANSACTION PERFORMANCE PAGE LOADING TEST")
    print("=" * 60)
    
    # Test linked pairs endpoint
    pairs = test_linked_pairs_endpoint()
    
    if not pairs:
        print("\nNo linked pairs found or endpoint failed.")
        print("This could explain why the performance page is not loading.")
        return
    
    print(f"\nFound {len(pairs)} linked transaction pairs:")
    for i, pair in enumerate(pairs[:3]):  # Show first 3 pairs
        print(f"  {i+1}. {pair.get('original', {}).get('security_ticker', 'N/A')} vs {pair.get('duplicate', {}).get('security_ticker', 'N/A')}")
    
    # Test performance comparison with first pair
    if pairs:
        first_pair_id = pairs[0].get("pair_id")
        if first_pair_id:
            success = test_performance_comparison_endpoint(first_pair_id)
            if success:
                print("\n✅ Performance comparison endpoint is working correctly")
            else:
                print("\n❌ Performance comparison endpoint failed")
        else:
            print("\n❌ First pair has no pair_id")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()