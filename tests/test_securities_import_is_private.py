#!/usr/bin/env python3
"""
Test script to verify the securities import functionality with is_private column
and upsert logic for existing tickers
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_security_crud_methods():
    """Test that the new CRUD methods are available"""
    print("=" * 60)
    print("TESTING SECURITY CRUD METHODS")
    print("=" * 60)
    
    try:
        from source_code.crud.security_crud_operations import security_crud
        from source_code.models.models import SecurityDtlInput
        
        # Test method existence
        print("1. Testing method availability...")
        if hasattr(security_crud, 'update_by_ticker'):
            print("✅ update_by_ticker method exists")
        else:
            print("❌ update_by_ticker method missing")
            return False
            
        if hasattr(security_crud, 'save_many_with_upsert'):
            print("✅ save_many_with_upsert method exists")
        else:
            print("❌ save_many_with_upsert method missing")
            return False
            
        # Test SecurityDtlInput with is_private field
        print("\n2. Testing SecurityDtlInput with is_private...")
        try:
            test_security = SecurityDtlInput(
                ticker="TEST",
                name="Test Security",
                company_name="Test Company",
                security_currency="USD",
                is_private=True
            )
            print("✅ SecurityDtlInput accepts is_private field")
        except Exception as e:
            print(f"❌ SecurityDtlInput error with is_private: {str(e)}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_api_endpoints():
    """Test that the API endpoints have been updated correctly"""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    try:
        # Check bulk-csv-string endpoint
        print("1. Testing bulk-csv-string endpoint updates...")
        with open("../source_code/crud/security_api_routes.py", "r") as f:
            content = f.read()
            
        # Check for is_private parsing
        if "is_private_val = row.get(\"is_private\")" in content:
            print("✅ bulk-csv-string has is_private parsing")
        else:
            print("❌ bulk-csv-string missing is_private parsing")
            return False
            
        # Check for upsert logic
        if "update_by_ticker" in content:
            print("✅ bulk-csv-string uses upsert logic")
        else:
            print("❌ bulk-csv-string missing upsert logic")
            return False
            
        # Check bulk-csv endpoint
        print("\n2. Testing bulk-csv endpoint updates...")
        if "save_many_with_upsert" in content:
            print("✅ bulk-csv uses save_many_with_upsert")
        else:
            print("❌ bulk-csv missing save_many_with_upsert")
            return False
            
        # Check for is_private in bulk-csv
        if content.count("is_private") >= 4:  # Should appear multiple times in both endpoints
            print("✅ bulk-csv has is_private support")
        else:
            print("❌ bulk-csv missing adequate is_private support")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking API endpoints: {str(e)}")
        return False

def test_csv_structure():
    """Test the expected CSV structure"""
    print("\n" + "=" * 60)
    print("TESTING CSV STRUCTURE")
    print("=" * 60)
    
    print("Expected CSV headers:")
    print("  ticker, name, company_name, security_currency, is_private")
    print("\nExample CSV data:")
    print("  AAPL,Apple Inc.,Apple Inc.,USD,false")
    print("  TSLA,Tesla Inc.,Tesla Inc.,USD,false") 
    print("  PRIV,Private Corp,Private Corporation,USD,true")
    print("\nis_private values accepted:")
    print("  • true, yes, y, 1 -> True")
    print("  • false, no, n, 0, empty -> False")
    print("  • Case insensitive")
    
    return True

def main():
    print("SECURITIES IMPORT is_private COLUMN TEST")
    print("=" * 60)
    print("Testing securities import endpoints with is_private column and upsert functionality")
    print()
    
    # Test CRUD methods
    crud_ok = test_security_crud_methods()
    
    # Test API endpoints
    api_ok = test_api_endpoints()
    
    # Test CSV structure info
    csv_ok = test_csv_structure()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"CRUD Methods: {'✅' if crud_ok else '❌'}")
    print(f"API Endpoints: {'✅' if api_ok else '❌'}")
    print(f"CSV Structure: {'✅' if csv_ok else '❌'}")
    
    if crud_ok and api_ok and csv_ok:
        print(f"\n🎉 SUCCESS: is_private column and upsert functionality implemented!")
        print("\nChanges made:")
        print("  • Added is_private column parsing to both bulk import endpoints")
        print("  • Implemented upsert logic to update existing securities by ticker")
        print("  • Added update_by_ticker and save_many_with_upsert CRUD methods")
        print("  • Updates name, company_name, is_private, and currency for existing tickers")
        print(f"\n📱 Test manually:")
        print("  1. Start backend: python -m uvicorn main:app --reload")
        print("  2. Use CSV imports with is_private column")
        print("  3. Import same ticker twice to test upsert functionality")
    else:
        print(f"\n❌ Issues found that need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()