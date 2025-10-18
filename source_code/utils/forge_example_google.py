import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict, Optional

# --- Configuration ---
BASE_URL = "https://forgeglobal.com/search-companies/"
HEADERS = {
    # It is good practice to identify your scraper.
    # Use a real browser user-agent to reduce the chance of being blocked.
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}
# A short delay between requests to be polite to the server and avoid rate limiting.
SCRAPE_DELAY_SECONDS = 1


def scrape_page(page_num: int) -> Optional[List[Dict]]:
    """
    Fetches, parses, and extracts company data from a single search results page.
    Returns a list of dictionaries containing company data, or None if no table is found.
    """
    if (page_num == 1):
        url = f"{BASE_URL}"
    else:
        url = f"{BASE_URL}?page={page_num}"

    print(f"-> Scraping page {page_num}: {url}")

    try:
        # Make the request to the target URL
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page_num}: {e}")
        return None

    # Pause for the specified delay
    time.sleep(SCRAPE_DELAY_SECONDS)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the main table containing the company listings.
    # NOTE: The selector below is based on standard Forge Global table structure.
    # If the site layout changes, this selector must be updated.
    table = soup.find('table', class_='table-responsive')

    if not table:
        # If the table is not found, we assume we have reached the end of the results.
        print(f"*** No results table found on page {page_num}. Assuming end of pagination. ***")
        return None

    # Extract column headers from the table header (<th> elements)
    headers = [th.text.strip() for th in table.find('thead').find_all('th')]

    # Extract data rows from the table body (<tr> elements)
    company_data = []

    # Get all rows in the table body
    rows = table.find('tbody').find_all('tr')

    for row in rows:
        # Get all data cells (<td> elements) in the row
        cols = row.find_all('td')
        if len(cols) == len(headers):
            # Create a dictionary mapping headers to cell data
            company_entry = {headers[i]: col.text.strip() for i, col in enumerate(cols)}
            # Add the current page number for context
            company_entry['Scrape Page'] = page_num
            company_data.append(company_entry)

    return company_data


def scrape_all_pages():
    """
    Controls the scraping process, iterating through all pages until the end is reached.
    """
    all_companies = []
    page = 1

    print("--- Starting Forge Global Company Search Scraper ---")

    while True:
        # Scrape the current page
        companies_on_page = scrape_page(page)

        if companies_on_page is None or not companies_on_page:
            # Termination condition: Stop if the function returned None (e.g., 404, no table found)
            # or if the list of companies is empty.
            print("--- Pagination complete. ---")
            break

        # Add the results to the main list
        all_companies.extend(companies_on_page)

        # Increment the page counter for the next loop iteration
        page += 1

    # Convert the collected data into a Pandas DataFrame for easy viewing and export
    if all_companies:
        df = pd.DataFrame(all_companies)
        print("\n--- Summary of Scraped Data ---")
        print(f"Total companies scraped: {len(df)}")
        print("\nFirst 5 entries:")
        print(df.head().to_markdown(index=False))

        # Optional: Save the data to a CSV file
        # df.to_csv('forge_companies.csv', index=False)
        # print("\nData also saved to 'forge_companies.csv'")
    else:
        print("No company data was successfully scraped.")


# Execute the main function when the script is run
if __name__ == "__main__":
    # Ensure necessary libraries are installed
    try:
        import requests
        import pandas
        import bs4
    except ImportError:
        print("Required libraries ('requests', 'beautifulsoup4', 'pandas') are not installed.")
        print("Please install them using: pip install requests beautifulsoup4 pandas")
    else:
        scrape_all_pages()
