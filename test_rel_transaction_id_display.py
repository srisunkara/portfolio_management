#!/usr/bin/env python3
"""
Test script to verify that rel_transaction_id is now showing up in the transactions list
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except:
        return False

def test_transactions_api():
    """Test the transactions API to see if rel_transaction_id is included"""
    print("Testing transactions API endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/transactions")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total transactions returned: {len(data)}")
            
            # Check if any transactions have rel_transaction_id
            transactions_with_rel_id = [t for t in data if t.get('rel_transaction_id') is not None]
            print(f"Transactions with rel_transaction_id: {len(transactions_with_rel_id)}")
            
            # Show sample data to verify structure
            if data:
                print("\nSample transaction structure:")
                sample = data[0]
                for key in sorted(sample.keys()):
                    value = sample[key]
                    if key == 'rel_transaction_id':
                        print(f"  {key}: {value} {'<-- THIS IS THE FIELD WE ARE TESTING' if value is not None else '<-- NULL/MISSING'}")
                    else:
                        print(f"  {key}: {value}")
            
            # If we have transactions with rel_transaction_id, show them
            if transactions_with_rel_id:
                print(f"\nTransactions with rel_transaction_id values:")
                for t in transactions_with_rel_id[:5]:  # Show first 5
                    print(f"  Transaction ID: {t.get('transaction_id')} -> rel_transaction_id: {t.get('rel_transaction_id')}")
            
            return len(transactions_with_rel_id) > 0
        else:
            print(f"API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error testing API: {e}")
        return False

def test_database_view_directly():
    """Test if we can verify the database view has been updated"""
    print("\nNote: The database view has been updated to include rel_transaction_id.")
    print("If the API test above shows transactions with rel_transaction_id values,")
    print("then the fix is working correctly.")
    print("If not, the database view may need to be recreated/refreshed.")

if __name__ == "__main__":
    print("=== Testing rel_transaction_id Display Issue ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("Server is running. Testing transactions API...")
    
    has_rel_transaction_id = test_transactions_api()
    
    test_database_view_directly()
    
    if has_rel_transaction_id:
        print("\n✅ SUCCESS: rel_transaction_id values are now showing up in the API response!")
        print("The frontend should now display these values in the transactions list.")
    else:
        print("\n❌ ISSUE: No transactions with rel_transaction_id found.")
        print("This could mean:")
        print("1. The database view needs to be recreated/refreshed")
        print("2. There are no transactions with rel_transaction_id values in the database")
        print("3. The server needs to be restarted to pick up the view changes")