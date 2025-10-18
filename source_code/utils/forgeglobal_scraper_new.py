"""
ForgeGlobal Search Companies Scraper

Description:
  Headless browser scraper that collects the tabular data from
  https://forgeglobal.com/search-companies/ across all pages and writes a CSV.

Why Playwright?
  The page is a modern client-side app. Data is rendered dynamically and may not
  be available via simple HTTP GET + HTML parsing. Playwright drives a real
  browser engine, ensuring robust extraction without reverse-engineering private APIs.

Requirements:
  - pip install -r requirements.txt
  - One-time browser download (first run):
      python -m playwright install

How to run:
  - As a module from the repository root:
      python -m source_code.utils.forgeglobal_scraper --out samples/forge_companies.csv
  - Or run directly:
      python source_code/utils/forgeglobal_scraper.py --out samples/forge_companies.csv

Notes:
  - The scraper attempts to discover table headers and map each row's cells to those
    headers, so if the site adds columns they will be included automatically.
  - It paginates by clicking the Next control until it is disabled/absent.
  - It includes resilience for slight UI changes (multiple selector strategies).

"""
from __future__ import annotations

import argparse
import csv
import re
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


URL = "https://forgeglobal.com/search-companies/"


@dataclass
class ScrapeConfig:
    url: str = URL
    timeout_ms: int = 15000  # wait timeout per operation
    headless: bool = True
    throttle_sec: float = 0.15  # small delay between pagination steps


class ForgeScraper:
    def __init__(self, cfg: ScrapeConfig):
        self.cfg = cfg

    def run(self) -> List[Dict[str, Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.cfg.headless)
            try:
                context = browser.new_context(
                    viewport={"width": 1366, "height": 900},
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                )
                page = context.new_page()
                page.set_default_timeout(self.cfg.timeout_ms)

                # First navigate to base URL to discover pagination (last page number)
                page.goto(self.cfg.url, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle")
                except Exception:
                    pass
                try:
                    self._dismiss_overlays(page)
                except Exception:
                    pass

                # Ensure the Trade Metrics table (or a generic table) is present
                self._wait_for_table(page)

                # Determine last page from hrefs like /search-companies/?page=
                last_page = self._get_last_page(page)
                if last_page < 1:
                    last_page = 1

                headers = self._extract_headers(page)
                if not headers:
                    raise RuntimeError("Failed to detect table headers on the page")

                all_rows: List[Dict[str, Any]] = []
                for page_idx in range(1, last_page + 1):
                    # Navigate via explicit page query parameter as requested
                    target_url = self.cfg.url if page_idx == 1 else f"{self.cfg.url}?page={page_idx}"
                    print(f"Navigating to page {page_idx} of {last_page}: {target_url}")
                    page.goto(target_url, wait_until="domcontentloaded")
                    try:
                        page.wait_for_load_state("networkidle")
                    except Exception:
                        pass
                    # Dismiss overlays that may reappear on each navigation (e.g., cookie banners)
                    try:
                        self._dismiss_overlays(page)
                    except Exception:
                        pass
                    # Wait for the table on each page
                    self._wait_for_table(page)
                    # Re-extract headers if they changed (defensive)
                    raw_headers = self._extract_headers(page) or headers
                    # Normalize headers to skip the first two non-data columns and start at 'Company'
                    norm_headers, skip_cols = self._normalize_headers_and_offset(raw_headers)
                    rows = self._extract_rows(page, norm_headers, skip_cols)
                    if rows:
                        print(f"Collected {len(rows)} rows from page {page_idx} of {last_page}")
                        all_rows.extend(rows)
                    else:
                        print(f"No rows found on page {page_idx}")
                    time.sleep(self.cfg.throttle_sec)

                return all_rows
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

    # -------- Internals --------
    def _wait_for_table(self, page) -> None:
        # Prefer table under/near a "Trade Metrics" heading if present
        try:
            tm = page.locator("text=Trade Metrics").first
            if tm and tm.count() > 0:
                # Look for a table in the same section/container
                # Try a few ancestor hops to find a nearby table
                for up in range(1, 5):
                    try:
                        container = tm.locator(f"xpath={'..' + '/..' * (up-1) if up>1 else '..'}")
                        if container and container.count() > 0:
                            tbl = container.locator("table, [role='table'], .mantine-Table-table, [data-table]")
                            if tbl and tbl.count() > 0:
                                tbl.first.wait_for(state="visible")
                                return
                    except Exception:
                        continue
        except Exception:
            pass
        # Fallback: generic table/grid selectors
        selectors = [
            "table",
            "[role='table']",
            "table[class*='table']",
            ".mantine-Table-table",
            "[data-table]",
        ]
        attempted = []
        last_err: Optional[Exception] = None
        for sel in selectors:
            attempted.append(sel)
            try:
                page.wait_for_selector(sel, state="visible")
                return
            except Exception as e:
                last_err = e
        # If table not found, try waiting for any row-like element in common grid structures
        row_selectors = [
            "tbody tr",
            "[role='row']",
            "div[role='rowgroup'] div[role='row']",
        ]
        for sel in row_selectors:
            attempted.append(sel)
            try:
                page.wait_for_selector(sel, state="visible")
                return
            except Exception as e:
                last_err = e
        raise PlaywrightTimeoutError(
            f"Could not locate a table on the page. Last attempted selectors: {attempted}. Last error: {last_err}"
        )

    def _get_last_page(self, page) -> int:
        """
        Inspect pagination links and derive the last page number from hrefs like
        "/search-companies/?page=123". Returns at least 1 if none found.
        """
        try:
            # Collect all anchors that contain the paging pattern
            links = page.locator("a[href*='/search-companies/?page=']").all()
            max_page = 1
            for a in links:
                href = a.get_attribute("href") or ""
                # Accept absolute or relative URLs
                idx = href.find("?page=")
                if idx == -1:
                    continue
                tail = href[idx + len("?page=") :]
                # Extract leading number
                num_str = ""
                for ch in tail:
                    if ch.isdigit():
                        num_str += ch
                    else:
                        break
                if num_str:
                    try:
                        num = int(num_str)
                        if num > max_page:
                            max_page = num
                    except Exception:
                        continue
            return max_page if max_page >= 1 else 1
        except Exception:
            return 1

    def _extract_headers(self, page) -> List[str]:
        # First, try <thead> th
        ths = page.locator("thead tr th").all()
        headers: List[str] = []
        if ths:
            headers = [self._norm_text(th.inner_text()) for th in ths]
            headers = [h for h in headers if h]
            if headers:
                return headers
        # Alternate: first row in table head or header role
        alt_ths = page.locator("[role='columnheader']").all()
        if alt_ths:
            headers = [self._norm_text(th.inner_text()) for th in alt_ths]
            headers = [h for h in headers if h]
            if headers:
                return headers
        # Fallback: get first row's cells as headers
        first_row_cells = page.locator("tbody tr").nth(0).locator("td").all()
        if first_row_cells:
            return [f"col_{i+1}" for i in range(len(first_row_cells))]
        return []

    def _normalize_headers_and_offset(self, raw_headers: List[str]) -> tuple[List[str], int]:
        """
        Normalize headers to skip the first two non-data columns ("Trade Metrics", "Last Funding Round")
        and start at the "Company" column if present. Returns a tuple of (normalized_headers, skip_cols).
        skip_cols indicates how many leading data cells to drop in each row to align with the normalized headers.
        """
        if not raw_headers:
            return raw_headers, 0
        # Case-insensitive compare
        lower = [h.strip().lower() for h in raw_headers]
        # Prefer starting at explicit "Company" column when found
        if "company" in lower:
            idx = lower.index("company")
            if idx > 0:
                return raw_headers[idx:], idx
        # Else, if first two known non-data columns are present, drop them
        if len(lower) >= 2 and lower[0].startswith("trade metrics") and lower[1].startswith("last funding"):
            return raw_headers[2:], 2
        # Default: no change
        return raw_headers, 0

    def _postprocess_row(self, headers: List[str], row_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Split the composite "Forge Price 1" column into three: Price, Change, Change %.
        Removes the original key if present. Returns the updated row_obj.
        """
        fp_key = None
        # find exact header match in a case-sensitive manner first, fallback to case-insensitive
        if "Forge Price 1" in row_obj:
            fp_key = "Forge Price 1"
        else:
            # try case-insensitive search
            for k in list(row_obj.keys()):
                if k.strip().lower() == "forge price 1":
                    fp_key = k
                    break
        if fp_key is None:
            return row_obj
        text = str(row_obj.get(fp_key) or "").strip()
        price, change, change_pct = self._parse_forge_price(text)
        row_obj["Forge Price 1 - Price"] = price
        row_obj["Forge Price 1 - Change"] = change
        row_obj["Forge Price 1 - Change %"] = change_pct
        # remove the original composite column to avoid confusion
        try:
            del row_obj[fp_key]
        except Exception:
            pass
        return row_obj

    def _parse_forge_price(self, text: str) -> tuple[str, str, str]:
        """
        Parse composite Forge Price cell text into (price, change, change%).
        Returns strings without currency symbols and without percent sign for change%.
        If parsing fails, returns empty strings.
        """
        if not text:
            return "", "", ""
        s = " ".join(str(text).split())
        # Price: first number, preferably with a currency symbol
        m_price = re.search(r"\$?\s*([0-9][\d,]*(?:\.\d+)?)", s)
        price = m_price.group(1).replace(",", "") if m_price else ""
        # Percent change: any number followed by % (take the first occurrence)
        m_pct = re.search(r"([+-]?\s*[0-9]+(?:\.\d+)?)\s*%", s)
        pct = m_pct.group(1).replace(" ", "") if m_pct else ""
        # Absolute change: first signed number that is not immediately followed by %
        m_change = None
        for m in re.finditer(r"([+-]\s*[0-9][\d,]*(?:\.\d+)?)", s):
            end = m.end()
            rest = s[end:]
            if re.match(r"\s*%", rest):
                # This one is actually the percentage
                continue
            m_change = m
            break
        change = m_change.group(1).replace(" ", "").replace(",", "") if m_change else ""
        return price, change, pct

    def _extract_rows(self, page, headers: List[str], skip_cols: int = 0) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        # Prefer standard table rows; if none, use ARIA row roles
        row_loc = page.locator("tbody tr")
        count = row_loc.count()
        if count == 0:
            row_loc = page.locator("[role='row']")
            count = row_loc.count()
        for i in range(count):
            tr = row_loc.nth(i)
            # Try standard table cells, then ARIA role cells
            tds = tr.locator("td").all()
            if not tds:
                # Some tables may not use tbody, try generic cells
                tds = tr.locator("[role='cell']").all()
            if not tds:
                continue
            row_vals: List[str] = []
            for td in tds:
                txt = self._norm_text(td.inner_text())
                # If the cell has a nested element (like span with up/down arrow), concatenate important parts
                if txt == "" or txt is None:
                    try:
                        txt = self._norm_text(td.text_content())
                    except Exception:
                        pass
                row_vals.append(txt)
            # Skip the leading non-data columns if requested
            if skip_cols and skip_cols > 0 and len(row_vals) > skip_cols:
                row_vals = row_vals[skip_cols:]
            # Align with headers length
            if len(row_vals) < len(headers):
                row_vals += [""] * (len(headers) - len(row_vals))
            if len(row_vals) > len(headers):
                row_vals = row_vals[: len(headers)]
            row_obj = {headers[j]: row_vals[j] for j in range(len(headers))}
            # Post-process special composite columns
            row_obj = self._postprocess_row(headers, row_obj)
            out.append(row_obj)
        return out

    def _dismiss_overlays(self, page) -> None:
        """
        Best-effort dismissal of common cookie/consent banners that block content.
        Non-fatal: ignores errors and timeouts.
        """
        candidates = [
            "button:has-text('Accept All')",
            "button:has-text('Accept')",
            "button:has-text('I Agree')",
            "button:has-text('Agree')",
            "button:has-text('Got it')",
            "button:has-text('Got It')",
            "button:has-text('Reject All')",
            "[role='button']:has-text('Accept')",
            "#onetrust-accept-btn-handler",
            "button[id*='accept']",
            "button.cookie-accept",
        ]
        for sel in candidates:
            try:
                btn = page.locator(sel).first
                if btn and btn.is_visible():
                    try:
                        btn.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    btn.click(timeout=1000)
                    # small delay to let layout update
                    time.sleep(0.05)
                    break
            except Exception:
                continue

    def _go_to_next_page(self, page) -> bool:
        # Try to find a next button; consider several selectors
        # 1) aria-label Next
        candidates = [
            "button[aria-label='Next']:not([disabled])",
            "a[aria-label='Next']",
            "button:has-text('Next'):not([disabled])",
            "a:has-text('Next')",
            "[role='button']:has-text('Next')",
            "li.pagination-next button:not([disabled])",
            "li.pagination-next a",
        ]
        for sel in candidates:
            btn = page.locator(sel)
            if btn.count() > 0 and btn.first.is_enabled():
                # Some buttons are present but hidden; ensure visible
                try:
                    btn.first.scroll_into_view_if_needed()
                except Exception:
                    pass
                try:
                    btn.first.click()
                    # wait for table update; a small heuristic: wait for any network idle + slight delay
                    page.wait_for_load_state("networkidle")
                    time.sleep(0.05)
                    return True
                except Exception:
                    # Try next selector
                    continue
        return False

    @staticmethod
    def _norm_text(s: Optional[str]) -> str:
        if s is None:
            return ""
        return " ".join(str(s).split())  # collapse whitespace


def write_csv(rows: List[Dict[str, Any]], out_path: Optional[str]) -> str:
    if not rows:
        raise RuntimeError("No data scraped; nothing to write.")

    # Compute header union to be safe if some pages had different structures
    headers: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                headers.append(k)

    # Default output path
    if not out_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join("samples", f"forge_companies_{ts}.csv")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return out_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape ForgeGlobal search companies data to CSV")
    parser.add_argument("--out", dest="out", default=None, help="Output CSV path (default: samples/forge_companies_<timestamp>.csv)")
    parser.add_argument("--headed", dest="headed", action="store_true", help="Run browser in headed mode (visible window)")
    parser.add_argument("--timeout", dest="timeout", type=int, default=15000, help="Timeout per operation in ms (default: 15000)")
    parser.add_argument("--throttle", dest="throttle", type=float, default=0.15, help="Delay between pages in seconds (default: 0.15)")

    args = parser.parse_args(argv)
    cfg = ScrapeConfig(headless=not args.headed, timeout_ms=args.timeout, throttle_sec=args.throttle)

    print(f"Starting scrape: {URL}")
    print("Tip: on first run, ensure browsers are installed via 'python -m playwright install'")

    try:
        scraper = ForgeScraper(cfg)
        rows = scraper.run()
        path = write_csv(rows, args.out)
        print(f"Done. Wrote {len(rows)} rows to: {path}")
        return 0
    except PlaywrightTimeoutError as te:
        print(f"Timeout while scraping: {te}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
