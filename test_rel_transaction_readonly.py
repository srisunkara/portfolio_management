#!/usr/bin/env python3
"""
Test script to verify the rel_transaction_id field implementation in TransactionDuplicate.jsx
This tests that the field is properly configured as read-only.
"""

def test_rel_transaction_id_readonly():
    """Test that rel_transaction_id field is configured as read-only"""
    
    # Read the TransactionDuplicate.jsx file
    file_path = "src/pages/transactions/TransactionDuplicate.jsx"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        print("=== Testing rel_transaction_id Read-Only Implementation ===\n")
        
        # Test 1: Check if rel_transaction_id condition exists
        has_rel_condition = 'if (name === "rel_transaction_id")' in content
        print(f"1. Has specific rel_transaction_id condition: {'✅ YES' if has_rel_condition else '❌ NO'}")
        
        # Test 2: Check if readOnly attribute is present
        has_readonly = 'readOnly' in content
        print(f"2. Has readOnly attribute: {'✅ YES' if has_readonly else '❌ NO'}")
        
        # Test 3: Check if read-only styling is applied
        has_readonly_style = 'backgroundColor: "#f8fafc"' in content and 'cursor: "not-allowed"' in content
        print(f"3. Has read-only styling: {'✅ YES' if has_readonly_style else '❌ NO'}")
        
        # Test 4: Check if the field is set with original transaction ID
        has_rel_initialization = 'initial[field.name] = originalTxn.transaction_id;' in content
        print(f"4. Field initialized with original transaction ID: {'✅ YES' if has_rel_initialization else '❌ NO'}")
        
        # Overall assessment
        all_tests_pass = has_rel_condition and has_readonly and has_readonly_style and has_rel_initialization
        
        print(f"\n=== Overall Assessment ===")
        if all_tests_pass:
            print("✅ SUCCESS: rel_transaction_id field is properly configured as read-only!")
            print("   - Field has specific handling condition")
            print("   - Field has readOnly attribute")
            print("   - Field has proper read-only styling")
            print("   - Field is initialized with original transaction ID")
        else:
            print("❌ ISSUES FOUND: Some tests failed")
            if not has_rel_condition:
                print("   - Missing specific rel_transaction_id condition")
            if not has_readonly:
                print("   - Missing readOnly attribute")
            if not has_readonly_style:
                print("   - Missing read-only styling")
            if not has_rel_initialization:
                print("   - Missing proper field initialization")
        
        return all_tests_pass
        
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find file {file_path}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_rel_transaction_id_readonly()
    exit(0 if success else 1)