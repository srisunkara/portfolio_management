#!/usr/bin/env python3
"""
Test script to verify all dependencies can be imported successfully.
This helps validate the requirements.txt file before Docker deployment.
"""

def test_imports():
    """Test importing all critical dependencies."""
    import_tests = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("psycopg2", "PostgreSQL adapter"),
        ("yfinance", "Financial data"),
        ("httpx", "HTTP client"),
        ("pytest", "Testing framework"),
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
        print(f"\n✅ All {len(import_tests)} critical dependencies imported successfully!")
        return True

def test_specific_imports():
    """Test specific imports that caused the original Docker error."""
    try:
        # This is the exact import chain that was failing
        from source_code.config import pg_db_conn_manager
        print("✅ Database connection manager import - OK")
        return True
    except ImportError as e:
        print(f"❌ Database connection manager import - FAILED: {e}")
        return False

if __name__ == "__main__":
    print("Testing dependencies from requirements.txt...\n")
    
    deps_ok = test_imports()
    print("\nTesting specific import chain that was failing...")
    specific_ok = test_specific_imports()
    
    if deps_ok and specific_ok:
        print("\n🎉 All tests passed! Requirements.txt should work for Docker deployment.")
        exit(0)
    else:
        print("\n💥 Some tests failed. Check the requirements.txt file.")
        exit(1)