# source_code/crud/security_price_api_routes.py
from datetime import datetime, date

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
import csv
import io
from fastapi.responses import Response

from source_code.crud.security_price_crud_operations import security_price_crud
from source_code.crud.security_crud_operations import security_crud
from source_code.models.models import SecurityPriceDtl, SecurityPriceDtlInput
from pydantic import BaseModel
import yfinance as yf

router = APIRouter(prefix="/security-prices", tags=["Security Prices"])

@router.get("/", response_model=list[SecurityPriceDtl])
def list_security_prices():
    return security_price_crud.list_all()

@router.get("/{security_price_id}", response_model=SecurityPriceDtl)
def get_security_price(security_price_id: int):
    p = security_price_crud.get_security(security_price_id)
    if not p:
        raise HTTPException(status_code=404, detail="Security price not found")
    return p

# Save single (server generates ID/timestamps)
@router.post("/", response_model=SecurityPriceDtl)
def save_security_price(price: SecurityPriceDtlInput):
    return security_price_crud.save(price)

# Bulk save JSON array
@router.post("/bulk", response_model=list[SecurityPriceDtl])
def save_security_prices_bulk(prices: list[SecurityPriceDtlInput]):
    if not prices:
        return []
    return security_price_crud.save_many(prices)

# CSV upload -> reuse bulk save
# Expected headers (case-insensitive): security_id, price_source_id, price_date, price, market_cap, [addl_notes] [price_currency]
@router.post("/bulk-csv", response_model=list[SecurityPriceDtl])
async def upload_security_prices_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        text = content_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"security_id", "price_source_id", "price_date", "price", "market_cap"}
        missing = required - set(headers)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")

        items: list[SecurityPriceDtlInput] = []
        row_num = 1
        for row in reader:
            row_num += 1
            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()

            try:
                security_id = int(get_val("security_id"))
                price_source_id = int(get_val("price_source_id"))
                price_date = get_val("price_date")  # FastAPI/Pydantic will parse ISO dates
                price = float(get_val("price"))
                market_cap = float(get_val("market_cap"))
                price_currency = (get_val("price_currency") or "USD").upper()
                # convert price_date to a date object if available. Otherwise, default today
                if price_date:
                    price_date = datetime.strptime(price_date, "%Y-%m-%d").date()
                else:
                    price_date = date.today()
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: numeric fields invalid")

            if not price_source_id:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: 'price_source_id' is required")

            addl_notes = get_val("addl_notes") or None

            items.append(SecurityPriceDtlInput(
                security_id=security_id,
                price_source_id=price_source_id,
                price_date=price_date,
                price=price,
                market_cap=market_cap,
                addl_notes=addl_notes,
                price_currency=price_currency,
            ))

        if not items:
            return []
        return security_price_crud.save_many(items)

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

# CSV export endpoint
@router.get("/export.csv")
def export_security_prices_csv() -> Response:
    items = security_price_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)

    header = ["security_price_id", "security_id", "price_source_id", "price_date", "price", "market_cap", "addl_notes", "price_currency", "created_ts", "last_updated_ts"]
    writer.writerow(header)
    for p in items:
        writer.writerow([
            getattr(p, "security_price_id", ""),
            getattr(p, "security_id", ""),
            getattr(p, "price_source_id", ""),
            getattr(p, "price_date", ""),
            getattr(p, "price", ""),
            getattr(p, "market_cap", ""),
            getattr(p, "addl_notes", ""),
            getattr(p, "price_currency", ""),
            getattr(p, "created_ts", ""),
            getattr(p, "last_updated_ts", ""),
        ])

    csv_data = output.getvalue()
    output.close()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="security_prices.csv"'}
    )

class DownloadPricesRequest(BaseModel):
    date: date

@router.post("/download")
def download_prices(req: DownloadPricesRequest) -> dict:
    """
    Download daily prices for all securities (by ticker) for a given date from Yahoo Finance
    and store them in security_price_dtl. Uses a fixed price_source_id=401 (Yahoo Finance).
    Skips securities without ticker or when price is unavailable for the date.
    """
    target_date = req.date
    ret_data = download_prices_by_date(target_date)
    return ret_data


def download_prices_by_date(target_date: date) -> dict:
    """
    Download daily prices for all securities (by ticker) for a given date from Yahoo Finance
    and store them in security_price_dtl. Uses a fixed price_source_id=401 (Yahoo Finance).
    Skips securities without a ticker or when the price is unavailable for the date.
    """
    securities = security_crud.list_all_public()
    attempted = 0
    saved = 0
    skipped = 0
    errors: list[str] = []
    YAHOO_SOURCE_ID = 1759649078984028  # Yahoo Finance pricing source ID

    # yfinance best practice: batch tickers when possible; but for simplicity and reliability here, iterate
    for s in securities:
        # Skip private securities
        if getattr(s, "is_private", False):
            skipped += 1
            continue
        ticker = (s.ticker or "").strip()
        if not ticker:
            skipped += 1
            continue
        attempted += 1
        try:
            tk = yf.Ticker(ticker)
            # fetch a small date window around the target to accommodate timezone differences
            start = target_date.strftime("%Y-%m-%d")
            end_dt = target_date.toordinal() + 1  # +1 day
            from datetime import date as _d, timedelta
            end = (_d.fromordinal(end_dt)).strftime("%Y-%m-%d")
            hist = tk.history(start=start, end=end, auto_adjust=False)
            if hist is None or len(hist) == 0:
                skipped += 1
                continue
            # Try to find a row matching date index; if not, take the last row (for some tickers intraday/UTC offsets)
            close_price = None
            # yfinance returns a pandas DataFrame; index may be Timestamp
            try:
                # exact date match
                if target_date.strftime("%Y-%m-%d") in [str(idx)[:10] for idx in hist.index]:
                    for idx, row in hist.iterrows():
                        if str(idx)[:10] == target_date.strftime("%Y-%m-%d"):
                            close_price = float(row.get("Close") or row.get("close"))
                            break
            except Exception:
                close_price = None
            if close_price is None:
                # fallback to last row
                last_row = hist.tail(1)
                if last_row is not None and len(last_row) > 0:
                    try:
                        close_price = float(last_row["Close"][0])
                    except Exception:
                        try:
                            close_price = float(last_row.iloc[0].get("Close") or last_row.iloc[0].get("close"))
                        except Exception:
                            close_price = None
            if close_price is None or not (close_price > 0):
                skipped += 1
                continue

            # Save price
            try:
                spi = SecurityPriceDtlInput(
                    security_id=s.security_id,
                    price_source_id=YAHOO_SOURCE_ID,
                    price_date=target_date,
                    price=round(close_price, 4),
                    market_cap=0.0,
                    addl_notes="Yahoo",
                    price_currency=(s.security_currency or "USD").upper(),
                )
                security_price_crud.save(spi)
                saved += 1
            except Exception as se:
                errors.append(f"save {ticker}: {se}")
        except Exception as e:
            errors.append(f"{ticker}: {e}")
            skipped += 1

    return {
        "date": target_date.isoformat(),
        "attempted": int(attempted),
        "saved": int(saved),
        "skipped": int(skipped),
        "errors": errors,
    }


@router.post("/download-date-range")
def download_prices_for_date_range(start_date: date, end_date: date):
    # get all weekday (Mon-Fri) dates between start_date and end_date
    dates = [d.date() for d in pd.date_range(start=start_date, end=end_date, freq="B")]
    for d in dates:
        download_prices_by_date(d)


@router.put("/{security_price_id}", response_model=SecurityPriceDtl)
def update_security_price(security_price_id: int, price: SecurityPriceDtlInput):
    try:
        return security_price_crud.update(security_price_id, price)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="Security price not found")

@router.delete("/{security_price_id}", response_model=dict)
def delete_security_price(security_price_id: int):
    if not security_price_crud.delete(security_price_id):
        raise HTTPException(status_code=404, detail="Security price not found")
    return {"deleted": True}


if __name__ == "__main__":
    download_prices_for_date_range(date(2025, 10, 1), date(2025, 10, 3))