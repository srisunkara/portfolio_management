#!/usr/bin/env python3
"""
Test script to diagnose blank page issue on localhost:8000
"""

import requests
import time
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_blank_page_issue():
    """Test the localhost:8000 endpoint and check for blank page issues"""
    
    print("=== Testing Blank Page Issue ===")
    
    # Test 1: Basic HTTP response
    print("\n1. Testing HTTP response...")
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
        
        if '<div id="root"></div>' in response.text:
            print("✓ React root div found in HTML")
        else:
            print("✗ React root div NOT found in HTML")
            
        if 'src="/assets/' in response.text:
            print("✓ Asset references found in HTML")
        else:
            print("✗ No asset references found in HTML")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ HTTP request failed: {e}")
        return False
    
    # Test 2: Asset availability
    print("\n2. Testing asset availability...")
    try:
        # Extract asset path from HTML
        import re
        asset_match = re.search(r'src="(/assets/[^"]+)"', response.text)
        if asset_match:
            asset_path = asset_match.group(1)
            asset_url = f"http://localhost:8000{asset_path}"
            print(f"Testing asset: {asset_url}")
            
            asset_response = requests.get(asset_url, timeout=10)
            print(f"Asset Status Code: {asset_response.status_code}")
            print(f"Asset Content Length: {len(asset_response.text)}")
            
            if asset_response.status_code == 200:
                print("✓ JavaScript asset is accessible")
            else:
                print("✗ JavaScript asset is NOT accessible")
        else:
            print("✗ Could not find asset path in HTML")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Asset request failed: {e}")
    
    # Test 3: Browser simulation (if selenium available)
    print("\n3. Testing with browser simulation...")
    try:
        # Setup Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            print("Opening localhost:8000...")
            driver.get("http://localhost:8000/")
            time.sleep(3)  # Wait for potential React rendering
            
            # Check if root div has content
            root_element = driver.find_element(By.ID, "root")
            root_html = root_element.get_attribute('innerHTML')
            
            print(f"Root div innerHTML length: {len(root_html)}")
            
            if root_html.strip():
                print("✓ Root div has content - React app is rendering")
                print(f"Content preview: {root_html[:200]}...")
            else:
                print("✗ Root div is EMPTY - React app is NOT rendering")
                
            # Check for any JavaScript errors in console
            logs = driver.get_log('browser')
            if logs:
                print(f"\nBrowser console logs ({len(logs)} entries):")
                for log in logs:
                    print(f"  {log['level']}: {log['message']}")
            else:
                print("No browser console logs found")
                
            # Check page title
            title = driver.title
            print(f"Page title: '{title}'")
            
        finally:
            driver.quit()
            
    except ImportError:
        print("Selenium not available - skipping browser simulation")
    except Exception as e:
        print(f"Browser simulation failed: {e}")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    test_blank_page_issue()