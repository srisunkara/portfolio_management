#!/usr/bin/env python3
"""
Test script to verify the duplicate prices fix in batch_upsert
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_batch_upsert_constraint_fix():
    """Test that batch_upsert now uses the correct ON CONFLICT clause"""
    print("=" * 60)
    print("TESTING DUPLICATE PRICES FIX")
    print("=" * 60)
    
    try:
        # Test import and method availability
        print("1. Testing module import...")
        from source_code.crud.security_price_crud_operations import security_price_crud
        print("✅ Module imported successfully")
        
        # Check that batch_upsert method exists
        print("2. Testing batch_upsert method exists...")
        if hasattr(security_price_crud, 'batch_upsert'):
            print("✅ batch_upsert method exists")
        else:
            print("❌ batch_upsert method missing")
            return False
            
        # Test the SQL query generation by inspecting the method
        print("3. Testing ON CONFLICT clause...")
        import inspect
        source_lines = inspect.getsourcelines(security_price_crud.batch_upsert)[0]
        source_code = ''.join(source_lines)
        
        if "ON CONFLICT (security_id, price_source_id, price_date)" in source_code:
            print("✅ ON CONFLICT uses natural key (security_id, price_source_id, price_date)")
        else:
            print("❌ ON CONFLICT not using natural key")
            return False
            
        if "ON CONFLICT (security_price_id)" in source_code:
            print("❌ Still using old ON CONFLICT (security_price_id)")
            return False
        else:
            print("✅ Old ON CONFLICT (security_price_id) removed")
            
        # Test UPDATE clause
        if "price = EXCLUDED.price" in source_code and "last_updated_ts = EXCLUDED.last_updated_ts" in source_code:
            print("✅ UPDATE clause correctly updates price fields")
        else:
            print("❌ UPDATE clause not properly configured")
            return False
            
        # Test with empty list (should not cause errors)
        print("4. Testing batch_upsert with empty list...")
        result = security_price_crud.batch_upsert([])
        if result == {"inserted": 0, "updated": 0, "total": 0}:
            print("✅ Empty batch upsert works correctly")
        else:
            print(f"❌ Unexpected result: {result}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_individual_save_consistency():
    """Test that the individual save method uses the same natural key logic"""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL SAVE CONSISTENCY")
    print("=" * 60)
    
    try:
        from source_code.crud.security_price_crud_operations import security_price_crud
        import inspect
        
        # Check individual save method
        source_lines = inspect.getsourcelines(security_price_crud.save)[0]
        source_code = ''.join(source_lines)
        
        if "WHERE security_id = %s AND price_source_id = %s AND price_date = %s" in source_code:
            print("✅ Individual save method uses same natural key check")
        else:
            print("❌ Individual save method inconsistent with batch method")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking individual save: {str(e)}")
        return False

def main():
    print("DUPLICATE PRICES FIX VERIFICATION")
    print("=" * 60)
    print("Testing that ON CONFLICT now uses (security_id, price_source_id, price_date)")
    print("instead of (security_price_id) to prevent duplicate prices")
    print()
    
    # Test batch upsert fix
    batch_fix_ok = test_batch_upsert_constraint_fix()
    
    # Test consistency with individual save
    consistency_ok = test_individual_save_consistency()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Batch Upsert Fix: {'✅' if batch_fix_ok else '❌'}")
    print(f"Method Consistency: {'✅' if consistency_ok else '❌'}")
    
    if batch_fix_ok and consistency_ok:
        print(f"\n🎉 SUCCESS: Duplicate prices fix implemented correctly!")
        print("\nChanges made:")
        print("  • Changed ON CONFLICT from (security_price_id) to (security_id, price_source_id, price_date)")
        print("  • This prevents duplicate prices for same security/source/date combination")
        print("  • Updated UPDATE clause to only update relevant price fields")
        print("  • Both individual save and batch upsert now use consistent natural key logic")
        print(f"\n📱 Price downloads should now update existing records instead of creating duplicates")
    else:
        print(f"\n❌ Issues found that need to be resolved")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()