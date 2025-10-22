#!/usr/bin/env python3
"""
Test script to check if the /transactions/linked-pairs API endpoint is working
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

def get_auth_token():
    """Get authentication token if needed"""
    try:
        response = requests.post(f"{BASE_URL}/users/login", json={
            "email": "test@example.com",
            "password": "demo"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except:
        pass
    return None

def test_linked_pairs_endpoint():
    """Test the linked-pairs API endpoint"""
    print("Testing /transactions/linked-pairs endpoint...")
    
    # Try without auth first
    try:
        response = requests.get(f"{BASE_URL}/transactions/linked-pairs")
        print(f"Status (no auth): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        elif response.status_code == 401:
            print("Authentication required, trying with auth token...")
            
            # Try with auth token
            token = get_auth_token()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{BASE_URL}/transactions/linked-pairs", headers=headers)
                print(f"Status (with auth): {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"Error response: {response.text}")
                    return False
            else:
                print("Could not get auth token")
                return False
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_transactions_endpoint():
    """Test basic transactions endpoint to see if any linked transactions exist"""
    print("\nTesting /transactions endpoint to check for linked transactions...")
    
    try:
        response = requests.get(f"{BASE_URL}/transactions")
        if response.status_code == 200:
            data = response.json()
            print(f"Total transactions: {len(data)}")
            
            # Check for transactions with rel_transaction_id
            linked_transactions = [t for t in data if t.get('rel_transaction_id') is not None]
            print(f"Transactions with rel_transaction_id: {len(linked_transactions)}")
            
            if linked_transactions:
                print("Sample linked transactions:")
                for t in linked_transactions[:3]:
                    print(f"  Transaction {t['transaction_id']} -> linked to {t['rel_transaction_id']}")
            else:
                print("No linked transactions found - this could be why linked-pairs returns empty")
                
            return len(linked_transactions) > 0
        else:
            print(f"Transactions endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing transactions endpoint: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Linked Transaction Pairs API ===")
    
    if not test_server_availability():
        print("ERROR: Server is not running or not accessible at localhost:8000")
        exit(1)
    
    print("Server is running. Testing endpoints...")
    
    # Test the specific endpoint that's failing
    linked_pairs_works = test_linked_pairs_endpoint()
    
    # Check if there are any linked transactions in the database
    has_linked_transactions = test_transactions_endpoint()
    
    print(f"\n=== Results ===")
    print(f"Linked pairs API works: {linked_pairs_works}")
    print(f"Has linked transactions: {has_linked_transactions}")
    
    if not linked_pairs_works:
        print("❌ The linked-pairs API is not working - this is the source of the frontend error")
    elif not has_linked_transactions:
        print("⚠️  The API works but there are no linked transactions to return")
    else:
        print("✅ Everything appears to be working correctly")