#!/usr/bin/env python3
"""
Test script to check if rel_transaction_id is visible in the transactions API response
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
            
            if data:
                print("\nFirst transaction fields:")
                sample = data[0]
                fields = sorted(sample.keys())
                
                # Check specifically for rel_transaction_id
                has_rel_field = 'rel_transaction_id' in fields
                print(f"rel_transaction_id field present: {has_rel_field}")
                
                if has_rel_field:
                    rel_value = sample.get('rel_transaction_id')
                    print(f"rel_transaction_id value: {rel_value}")
                
                # Show all fields for debugging
                print(f"\nAll available fields ({len(fields)}):")
                for i, field in enumerate(fields):
                    value = sample[field]
                    marker = " <-- REL_TRANSACTION_ID" if field == 'rel_transaction_id' else ""
                    print(f"  {i+1:2d}. {field}: {value}{marker}")
                
                # Count transactions with rel_transaction_id values
                transactions_with_rel_id = [t for t in data if t.get('rel_transaction_id') is not None]
                print(f"\nTransactions with rel_transaction_id values: {len(transactions_with_rel_id)}")
                
                if transactions_with_rel_id:
                    print("Examples:")
                    for t in transactions_with_rel_id[:3]:
                        print(f"  Transaction {t.get('transaction_id')} -> rel_transaction_id: {t.get('rel_transaction_id')}")
                
                return has_rel_field
            else:
                print("No transactions found in response")
                return False
        else:
            print(f"API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error testing API: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing rel_transaction_id Visibility Issue ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("Server is running. Testing transactions API...")
    
    has_rel_field = test_transactions_api()
    
    if has_rel_field:
        print("\n✅ SUCCESS: rel_transaction_id field is present in API response!")
        print("If it's still not visible on the frontend, the issue might be:")
        print("1. Frontend caching - try hard refresh (Ctrl+F5)")
        print("2. Field ordering/positioning in the table")
        print("3. CSS styling hiding the column")
    else:
        print("\n❌ ISSUE: rel_transaction_id field is missing from API response")
        print("The backend or database view needs to be checked")