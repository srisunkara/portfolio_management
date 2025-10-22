#!/usr/bin/env python3
"""
Test script to verify that pydantic email validation works correctly.
This helps validate that the email-validator dependency is properly installed.
"""

def test_email_validation():
    """Test pydantic EmailStr functionality."""
    try:
        from pydantic import BaseModel, EmailStr
        print("✅ Successfully imported EmailStr from pydantic")
        
        # Test creating a model with EmailStr
        class TestModel(BaseModel):
            email: EmailStr
        
        # Test valid email
        try:
            valid_model = TestModel(email="test@example.com")
            print(f"✅ Valid email validation works: {valid_model.email}")
        except Exception as e:
            print(f"❌ Valid email validation failed: {e}")
            return False
        
        # Test invalid email (should raise validation error)
        try:
            invalid_model = TestModel(email="invalid-email")
            print(f"❌ Invalid email validation should have failed but didn't: {invalid_model.email}")
            return False
        except Exception as e:
            print(f"✅ Invalid email properly rejected: {type(e).__name__}")
        
        print("✅ EmailStr validation is working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import EmailStr: {e}")
        return False

def test_specific_import():
    """Test the specific import that was causing the Docker error."""
    try:
        # This mirrors the import from user_api_routes.py
        from pydantic import BaseModel, EmailStr
        
        # Test the exact pattern used in the codebase
        class LoginRequest(BaseModel):
            email: EmailStr
            password: str
        
        # Test with valid data
        login_data = LoginRequest(email="user@example.com", password="secret")
        print(f"✅ Login request model works: email={login_data.email}")
        return True
        
    except Exception as e:
        print(f"❌ Login request model failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing pydantic email validation functionality...\n")
    
    email_ok = test_email_validation()
    print("\nTesting specific use case from codebase...")
    specific_ok = test_specific_import()
    
    if email_ok and specific_ok:
        print("\n🎉 All email validation tests passed! Docker deployment should work now.")
        exit(0)
    else:
        print("\n💥 Email validation tests failed. Check the pydantic[email] dependency.")
        exit(1)