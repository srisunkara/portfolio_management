"""
Utility to load security prices from a CSV file into security_price_dtl.

Expected input columns (case-insensitive, flexible names):
- Date (also accepts date, price_date)
- Ticker (also accepts symbol)
- Open (open_px)
- High (high_px)
- Low (low_px)
- Close (close_px / used as primary price)
- Volume
- Adj Close (adj_close, adj_close_px)

Each row is mapped to a SecurityPriceDtlInput. Ticker is resolved to security_id
using security_dtl. Unknown tickers are skipped. The loader uses batch upsert for
performance and returns a summary dict (counts and a few sample details).

Example CSV line:
Date,Ticker,Open,High,Low,Close,Volume,Adj Close
2024-01-02 00:00:00,AA,32.8082,33.2387,32.3287,32.5929,3838000.0,nan
"""
from __future__ import annotations

import csv
from datetime import datetime, date as _date
from typing import Dict, Any, Tuple, List

from source_code.crud.security_crud_operations import security_crud
from source_code.crud.security_price_crud_operations import security_price_crud
from source_code.models.models import SecurityPriceDtlInput

# Default price source id (Yahoo Finance) used elsewhere in the codebase
DEFAULT_PRICE_SOURCE_ID = 1759649078984028


def _normalize_header(h: str) -> str:
    return (h or "").strip().lower().replace(" ", "_")


def _get_row_val(row: Dict[str, str], *keys: str) -> str:
    # Try multiple header variants in a case-insensitive and underscore-insensitive way
    normalized = { _normalize_header(k): v for k, v in row.items() }
    for k in keys:
        v = normalized.get(_normalize_header(k))
        if v is not None:
            return v
    return ""


def _parse_date(s: str) -> _date | None:
    s = (s or "").strip()
    if not s:
        return None
    fmts = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f).date()
        except Exception:
            pass
    # try only the first 10 chars if looks like ISO datetime
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_float(s: str) -> float | None:
    s = (s or "").strip()
    if not s or s.lower() in {"nan", "na", "null", "none"}:
        return None
    s = s.replace(",", "")  # handle thousands separators
    try:
        return float(s)
    except Exception:
        return None


def _load_ticker_map(include_private: bool = False) -> Dict[str, Dict[str, Any]]:
    """Return mapping of UPPER ticker -> security record (as dict-like model)."""
    securities = security_crud.list_all() if include_private else security_crud.list_all_public()
    out: Dict[str, Any] = {}
    for s in securities:
        t = (getattr(s, "ticker", None) or "").upper().strip()
        if t:
            out[t] = s
    return out


def load_security_prices_from_file(
    file_path: str,
    price_source_id: int = DEFAULT_PRICE_SOURCE_ID,
    default_currency: str = "USD",
    addl_notes: str | None = "CSV Loader",
    include_private: bool = False,
) -> Dict[str, Any]:
    """
    Load security prices from CSV at file_path and upsert into security_price_dtl.

    Returns a summary dict with counts and samples.
    """
    ticker_map = _load_ticker_map(include_private=include_private)

    total_rows = 0
    prepared = 0
    skipped_unknown_ticker: List[str] = []
    skipped_bad_data: List[Tuple[int, str]] = []  # (row_num, reason)
    # Deduplicate by natural key (security_id, price_source_id, price_date)
    inputs_by_key: Dict[tuple, SecurityPriceDtlInput] = {}

    # Read CSV with DictReader to support header names
    with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {
                "read": 0,
                "prepared": 0,
                "total": 0,
                "inserted": 0,
                "updated": 0,
                "skipped_unknown_ticker": [],
                "skipped_bad_data": ["Missing headers"],
            }

        for idx, row in enumerate(reader, start=2):  # start=2 because header is line 1
            total_rows += 1
            dt_str = _get_row_val(row, "date", "price_date")
            ticker = (_get_row_val(row, "ticker", "symbol") or "").upper().strip()
            open_px = _parse_float(_get_row_val(row, "open", "open_px"))
            high_px = _parse_float(_get_row_val(row, "high", "high_px"))
            low_px = _parse_float(_get_row_val(row, "low", "low_px"))
            close_px = _parse_float(_get_row_val(row, "close", "close_px"))
            adj_close_px = _parse_float(_get_row_val(row, "adj_close", "adj close", "adj_close_px"))
            volume = _parse_float(_get_row_val(row, "volume"))

            # if volume or adj close are not numbers, default to null
            if volume is not None and not volume.is_integer():
                volume = None
            if adj_close_px is not None and not adj_close_px.is_integer():
                adj_close_px = None

            d = _parse_date(dt_str)
            if not d or not ticker or close_px is None:
                skipped_bad_data.append((idx, f"Missing/invalid required fields (date/ticker/close). Raw: date='{dt_str}', ticker='{ticker}'"))
                continue

            sec = ticker_map.get(ticker)
            if not sec:
                skipped_unknown_ticker.append(ticker)
                continue

            # Price currency: prefer security currency if available
            price_currency = (getattr(sec, "security_currency", None) or default_currency).upper()

            spi = SecurityPriceDtlInput(
                security_id=sec.security_id,
                price_source_id=price_source_id,
                price_date=d,
                price=close_px,
                open_px=open_px,
                close_px=close_px,
                high_px=high_px,
                low_px=low_px,
                adj_close_px=adj_close_px,
                volume=volume,
                market_cap=0.0,
                addl_notes=addl_notes,
                price_currency=price_currency,
            )
            key = (sec.security_id, price_source_id, d)
            inputs_by_key[key] = spi  # keep last occurrence
            prepared += 1

    price_inputs: List[SecurityPriceDtlInput] = list(inputs_by_key.values())
    if not price_inputs:
        return {
            "read": total_rows,
            "prepared": 0,
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "skipped_unknown_ticker": sorted(list(set(skipped_unknown_ticker))),
            "skipped_bad_data": skipped_bad_data,
            "message": "No valid rows to upsert"
        }

    # Perform batch upsert
    try:
        result = security_price_crud.batch_upsert(price_inputs)
    except Exception as e:
        # Fallback to per-row save to salvage partial success
        inserted = 0
        for spi in price_inputs:
            try:
                security_price_crud.save(spi)
                inserted += 1
            except Exception:
                pass
        result = {"inserted": inserted, "updated": 0, "total": len(price_inputs), "fallback": True}

    summary = {
        "read": total_rows,
        "prepared": prepared,
        "total": result.get("total", len(price_inputs)),
        "inserted": result.get("inserted", 0),
        "updated": result.get("updated", 0),
        "skipped_unknown_ticker": sorted(list(set(skipped_unknown_ticker))),
        "skipped_unknown_ticker_count": len(set(skipped_unknown_ticker)),
        "skipped_bad_data": skipped_bad_data[:20],  # limit to first 20 entries in summary
    }

    print("Security Price Loader Summary:")
    print(summary)
    return summary


__all__ = ["load_security_prices_from_file", "DEFAULT_PRICE_SOURCE_ID"]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load security prices from a CSV file by ticker")
    parser.add_argument("csv_path", help="Path to CSV file with columns: Date,Ticker,Open,High,Low,Close,Volume,Adj Close")
    parser.add_argument("--source-id", type=int, default=DEFAULT_PRICE_SOURCE_ID, help="Price source id (default: Yahoo Finance id)")
    parser.add_argument("--currency", default="USD", help="Default price currency if security has none (default: USD)")
    parser.add_argument("--notes", default="CSV Loader", help="Additional notes stored with each price row")
    parser.add_argument("--include-private", action="store_true", help="Include private securities when resolving tickers")

    args = parser.parse_args()
    summary = load_security_prices_from_file(
        args.csv_path,
        price_source_id=args.source_id,
        default_currency=args.currency,
        addl_notes=args.notes,
        include_private=args.include_private,
    )
    # Pretty print summary
    import json
    print(json.dumps(summary, indent=2, default=str))
