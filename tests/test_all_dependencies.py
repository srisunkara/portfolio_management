#!/usr/bin/env python3
"""
Comprehensive test script to verify all dependencies can be imported successfully.
This helps validate the complete requirements.txt file before Docker deployment.
"""

def test_all_imports():
    """Test importing all dependencies listed in requirements.txt."""
    import_tests = [
        # Web Framework
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("multipart", "Python multipart form data parsing (python-multipart)"),
        ("starlette", "ASGI framework/toolkit"),
        
        # Database
        ("psycopg2", "PostgreSQL adapter"),
        
        # Data Models and Validation
        ("pydantic", "Data validation"),
        ("email_validator", "Email validation (from pydantic[email])"),
        
        # HTTP Client
        ("httpx", "HTTP client"),
        
        # Financial Data
        ("yfinance", "Yahoo Finance data"),
        ("pandas", "Data analysis library"),
        
        # Testing
        ("pytest", "Testing framework"),
        
        # Web Automation
        ("playwright", "Browser automation"),
    ]
    
    failed_imports = []
    
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            print(f"✅ {module_name} ({description}) - OK")
        except ImportError as e:
            failed_imports.append((module_name, description, str(e)))
            print(f"❌ {module_name} ({description}) - FAILED: {e}")
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} dependencies failed to import:")
        for module_name, description, error in failed_imports:
            print(f"   - {module_name}: {error}")
        return False
    else:
        print(f"\n✅ All {len(import_tests)} dependencies imported successfully!")
        return True

def test_specific_functionality():
    """Test specific functionality that uses the dependencies."""
    try:
        # Test pandas functionality used in the codebase
        import pandas as pd
        from datetime import date
        
        # Test business day range (used in security_price_api_routes.py)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        business_days = pd.bdate_range(start=start_date, end=end_date)
        print(f"✅ Pandas business day range works: {len(business_days)} business days")
        
        # Test date range (also used in security_price_api_routes.py)
        dates = [d.date() for d in pd.date_range(start=start_date, end=end_date, freq="B")]
        print(f"✅ Pandas date range works: {len(dates)} dates")
        
        # Test pydantic email validation
        from pydantic import BaseModel, EmailStr
        
        class TestModel(BaseModel):
            email: EmailStr
        
        test_model = TestModel(email="test@example.com")
        print(f"✅ Pydantic email validation works: {test_model.email}")
        
        # Test database connection manager import
        from source_code.config import pg_db_conn_manager
        print("✅ Database connection manager import works")
        
        return True
        
    except Exception as e:
        print(f"❌ Specific functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing all dependencies from requirements.txt...\n")
    
    all_deps_ok = test_all_imports()
    print("\nTesting specific functionality...")
    functionality_ok = test_specific_functionality()
    
    if all_deps_ok and functionality_ok:
        print("\n🎉 All tests passed! Requirements.txt is complete and ready for Docker deployment.")
        exit(0)
    else:
        print("\n💥 Some tests failed. Check the requirements.txt file for missing dependencies.")
        exit(1)