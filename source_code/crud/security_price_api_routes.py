# source_code/crud/security_price_api_routes.py
import csv
import io
import os
import shutil
import tempfile
from datetime import date
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from source_code.crud.security_crud_operations import security_crud
from source_code.crud.security_price_crud_operations import security_price_crud
from source_code.models.models import SecurityPriceDtl, SecurityPriceDtlInput
from source_code.utils import security_price_loader
from source_code.utils.security_data_by_yfinance import get_historical_data_list

router = APIRouter(prefix="/api/security-prices", tags=["Security Prices"])

@router.get("", response_model=list[SecurityPriceDtl])
@router.get("/", response_model=list[SecurityPriceDtl])
def list_security_prices(
    date: date | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    ticker: str | None = None
):
    # Support legacy single date parameter for backward compatibility
    if date is not None:
        return security_price_crud.list_by_date(date)
    
    # New date range and ticker filtering
    if from_date is not None or to_date is not None or ticker is not None:
        return security_price_crud.list_by_date_range_and_ticker(from_date, to_date, ticker)
    
    # Performance optimization: Never load all records without filters
    # Default to last 7 days if no filters provided to prevent slow loading
    from datetime import date as _date, timedelta
    default_to_date = _date.today()
    default_from_date = default_to_date - timedelta(days=7)
    return security_price_crud.list_by_date_range_and_ticker(default_from_date, default_to_date, None)

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
# Expected headers (case-insensitive): security_id, price_source_id, price_date, price, [open_px] [close_px] [high_px] [low_px] [adj_close_px] [volume] [market_cap] [addl_notes] [price_currency]
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
        required = {"security_id", "price_source_id", "price_date", "price"}
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
                market_cap_str = get_val("market_cap")
                market_cap = float(market_cap_str) if market_cap_str else 0.0
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

            # Optional extended price fields
            def parse_float_opt(v: str) -> float | None:
                try:
                    return float(v) if v not in (None, "") else None
                except Exception:
                    return None
            open_px = parse_float_opt(get_val("open_px"))
            close_px = parse_float_opt(get_val("close_px"))
            high_px = parse_float_opt(get_val("high_px"))
            low_px = parse_float_opt(get_val("low_px"))
            adj_close_px = parse_float_opt(get_val("adj_close_px"))
            volume = parse_float_opt(get_val("volume"))

            items.append(SecurityPriceDtlInput(
                security_id=security_id,
                price_source_id=price_source_id,
                price_date=price_date,
                price=price,
                open_px=open_px,
                close_px=close_px,
                high_px=high_px,
                low_px=low_px,
                adj_close_px=adj_close_px,
                volume=volume,
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

    header = [
        "security_price_id", "security_id", "price_source_id", "price_date", "price",
        "open_px", "close_px", "high_px", "low_px", "adj_close_px", "volume",
        "market_cap", "addl_notes", "price_currency", "created_ts", "last_updated_ts"
    ]
    writer.writerow(header)
    for p in items:
        writer.writerow([
            getattr(p, "security_price_id", ""),
            getattr(p, "security_id", ""),
            getattr(p, "price_source_id", ""),
            getattr(p, "price_date", ""),
            getattr(p, "price", ""),
            getattr(p, "open_px", ""),
            getattr(p, "close_px", ""),
            getattr(p, "high_px", ""),
            getattr(p, "low_px", ""),
            getattr(p, "adj_close_px", ""),
            getattr(p, "volume", ""),
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
    from_date: date | None = None
    to_date: date | None = None  
    tickers: list[str] | None = None
    save_to_file: bool = False
    delete_after_download: bool = False
    incl_missing_securities_only: bool = False
    price_source_id: int | None = None

@router.post("/download-date-range")
def download_date_range(req: DownloadPricesRequest) -> dict:
    """
    Download daily prices for securities (by ticker) for a date range from Yahoo Finance
    and store them in security_price_dtl. Uses a fixed price_source_id (Yahoo Finance).
    Defaults to last work day to today if no dates provided.
    Can filter by ticker list or download for all securities in database.
    """
    # Set default date range: last work day to today
    today = datetime.now().date()
    if req.to_date is None:
        to_date = today
    else:
        to_date = req.to_date
    
    if req.from_date is None:
        # Get last work day (Monday if today is weekend, otherwise previous day if workday)
        if today.weekday() == 0:  # Monday
            from_date = today - timedelta(days=3)  # Previous Friday
        elif today.weekday() == 6:  # Sunday  
            from_date = today - timedelta(days=2)  # Previous Friday
        else:
            from_date = today - timedelta(days=1)  # Previous day
    else:
        from_date = req.from_date

    ticker_list = req.tickers or []
    # dict of securities based on Ticker to get the security_id
    security_data_list = []
    if req.tickers is None:
        # Get securities to process
        if req.incl_missing_securities_only:
            print("Getting all public securities that do not have any price between the selected date range.")
            security_data_list = security_crud.list_all_public_with_missing_prices(from_date, to_date)
        else:
            print("Getting all public securities")
            security_data_list = security_crud.list_all_public()
    else:
        # get security data for all tickers in the list
        # Preserve current behavior: restrict to public securities when tickers are provided
        security_data_list = security_crud.list_all_by_ticker(req.tickers, public_only=True)

    print("No of securities: ", len(security_data_list))
    # get a unique list of tickers
    ticker_list_set = {s.ticker.upper().strip() for s in security_data_list if s.ticker}
    ticker_list = list(ticker_list_set)

    # get price history for the selected date range
    from_date_str = from_date.isoformat()
    to_date_str = to_date.isoformat()
    # data_list output will be a list of dictionaries with columns: ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', "Adj Close"]
    data_list, cols_to_keep = get_historical_data_list(ticker_list, from_date_str, to_date_str)
    # build a list of SecurityPriceDtlInput
    # Prepare price input for batch processing
    price_inputs = []
    if data_list is None or len(data_list) == 0:
        return {"message": "No price data available for the selected date range"}

    if req.save_to_file:
        # write data_list as csv to a file with current timestamp as filename
        filename = f"security_price_data_{from_date.isoformat()}_{to_date.isoformat()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        print(f">>> Saving data to file {filename}")
        with open(filename, "w") as f:
            writer = csv.writer(f)
            writer.writerow(cols_to_keep)
            for row in data_list:
                # write data from each row, which is a dictionary to the csv file based on the header info
                # (iterate over the cols list and write in the order of cols
                writer.writerow([row[col] for col in cols_to_keep])

        # once downloaded, load prices to the database using the security_price_loader (similar to load_prices_from_file)
        ret_data = security_price_loader.load_security_prices_from_file(filename)

        if req.delete_after_download:
            print(f">>> Deleting downloaded file {filename}")
            os.remove(filename)
    else:
        ret_data = security_price_loader.load_security_prices_from_list_of_dicts(data_list)

    # add input parameters to the returned data
    ret_data["from_date"] = from_date.isoformat()
    ret_data["to_date"] = to_date.isoformat()
    ret_data["tickers"] = ticker_list

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

            # Save price with extended OHLC fields
            try:
                # Derive extended fields from matched row/last row similar to above
                open_px = None
                close_px = None
                high_px = None
                low_px = None
                adj_close_px = None
                volume = None
                try:
                    matched = False
                    if target_date.strftime("%Y-%m-%d") in [str(idx)[:10] for idx in hist.index]:
                        for idx, row in hist.iterrows():
                            if str(idx)[:10] == target_date.strftime("%Y-%m-%d"):
                                open_px = float(row.get("Open") or row.get("open") or 0)
                                close_px = float(row.get("Close") or row.get("close") or 0)
                                high_px = float(row.get("High") or row.get("high") or 0)
                                low_px = float(row.get("Low") or row.get("low") or 0)
                                adj_close_px = float(row.get("Adj Close") or row.get("Adj_Close") or row.get("adj_close") or 0)
                                volume = float(row.get("Volume") or row.get("volume") or 0)
                                matched = True
                                break
                    if not matched:
                        lr = hist.tail(1)
                        if lr is not None and len(lr) > 0:
                            r = lr.iloc[0]
                            open_px = float(r.get("Open") or r.get("open") or 0)
                            close_px = float(r.get("Close") or r.get("close") or 0)
                            high_px = float(r.get("High") or r.get("high") or 0)
                            low_px = float(r.get("Low") or r.get("low") or 0)
                            adj_close_px = float(r.get("Adj Close") or r.get("Adj_Close") or r.get("adj_close") or 0)
                            volume = float(r.get("Volume") or r.get("volume") or 0)
                except Exception:
                    pass

                spi = SecurityPriceDtlInput(
                    security_id=s.security_id,
                    price_source_id=YAHOO_SOURCE_ID,
                    price_date=target_date,
                    price=round(close_price, 4),
                    open_px=open_px,
                    close_px=close_px,
                    high_px=high_px,
                    low_px=low_px,
                    adj_close_px=adj_close_px,
                    volume=volume,
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

@router.post("/load_prices_from_file")
def load_prices_from_file(file: UploadFile = File(...)):
    """
    Load security prices from a CSV file, sent from the REST API request.

    Returns:
        dict: A dictionary indicating the success of the operation.
    """
    # save the file to local temp directory and call load_security_prices_from_file from security_price_loader utility
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        ret_data = security_price_loader.load_security_prices_from_file(temp_file_path)
        return ret_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading prices: {str(e)}")


if __name__ == "__main__":
    # download_prices_for_date_range(date(2025, 10, 1), date(2025, 10, 3))
    print("Starting")