# source_code/crud/security_api.py
from fastapi import APIRouter, HTTPException, Body
from fastapi import UploadFile, File
import csv
import io
from fastapi.responses import Response

from source_code.crud.security_crud_operations import security_crud
from source_code.models.models import SecurityDtl, SecurityDtlInput
from source_code.utils import security_data_by_yahooquery, domain_utils

router = APIRouter(prefix="/api/securities", tags=["Securities"])


@router.post("/", response_model=SecurityDtl)
def save_security(security: SecurityDtlInput):
    print(security)
    return security_crud.save(security)

# Bulk load endpoint: accepts a JSON array of SecurityDtlInput and returns created SecurityDtl items
@router.post("/bulk", response_model=list[SecurityDtl])
def save_securities_bulk(securities: list[SecurityDtlInput]):
    if not securities:
        return []
    return security_crud.save_many(securities)

# Bulk save with comma separated values (CSV)
# Expected headers (case-insensitive): ticker, name, company_name, [security_currency]
@router.post("/bulk-csv-string")
def save_securities_bulk_csv_string(body: str = Body(..., media_type="text/plain")) -> dict:
    """
    Accept raw CSV text in the request body (Content-Type: text/plain) and bulk create securities.
    Behavior:
    - Check by ticker (case-insensitive) against existing securities first; skip if exists.
    - Skip duplicate tickers within the same request.
    - If a row is invalid (missing required fields), skip it.
    - If saving one security fails, skip it and continue.
    Returns a summary status with counts; does not return lists of securities.
    Expected headers (case-insensitive): ticker, name, company_name, [security_currency], [is_private]
    """
    try:
        if not body or not str(body).strip():
            return {"status": "ok", "received": 0, "attempted": 0, "added": 0, "skipped_existing": 0, "skipped_duplicate_in_request": 0, "skipped_invalid": 0, "errors": 0}
        # Normalize newlines and feed to CSV reader
        text = str(body).replace("\r\n", "\n").replace("\r", "\n")
        reader = csv.DictReader(io.StringIO(text))
        # Validate headers
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"ticker", "name", "company_name"}
        if not required.issubset(set(headers)):
            missing = ", ".join(sorted(required - set(headers)))
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {missing}")

        def parse_bool(v: str) -> bool:
            if v is None:
                return False
            s = str(v).strip().lower()
            return s in {"1", "true", "yes", "y"}

        # Build existing ticker set (case-insensitive)
        try:
            existing_tickers = { (s.ticker or "").strip().lower() for s in security_crud.list_all() }
        except Exception:
            existing_tickers = set()

        seen_in_request: set[str] = set()
        received = 0
        attempted = 0
        added = 0
        skipped_existing = 0
        skipped_duplicate_in_request = 0
        skipped_invalid = 0
        errors = 0
        
        # Track ticker lists for summary
        added_tickers = []
        skipped_tickers = []
        failed_tickers = []

        for row in reader:
            received += 1
            ticker = (row.get("ticker") or row.get("TICKER") or row.get("Ticker") or "").strip()
            name = (row.get("name") or row.get("NAME") or row.get("Name") or "").strip()
            company_name = (row.get("company_name") or row.get("COMPANY_NAME") or row.get("Company_Name") or "").strip()
            currency = ((row.get("security_currency") or row.get("SECURITY_CURRENCY") or row.get("Security_Currency") or "USD").strip() or "USD").upper()
            is_private_val = row.get("is_private") or row.get("IS_PRIVATE") or row.get("Is_Private")
            is_private = parse_bool(is_private_val)

            if not ticker or not name or not company_name:
                skipped_invalid += 1
                if ticker:  # Only add to skipped list if we have a ticker
                    skipped_tickers.append(ticker)
                continue

            key = ticker.lower()
            if key in seen_in_request:
                skipped_duplicate_in_request += 1
                skipped_tickers.append(ticker)
                continue

            attempted += 1
            try:
                norm = SecurityDtlInput(
                    ticker=ticker,
                    name=name,
                    company_name=company_name,
                    security_currency=currency,
                    is_private=is_private,
                )
                # Use upsert logic to update existing securities or create new ones
                if key in existing_tickers:
                    security_crud.update_by_ticker(ticker, norm)
                    skipped_existing += 1
                    skipped_tickers.append(ticker)
                else:
                    security_crud.save(norm)
                    existing_tickers.add(key)
                    added += 1
                    added_tickers.append(ticker)
                seen_in_request.add(key)
            except Exception:
                errors += 1
                failed_tickers.append(ticker)
                # do not add to seen/existing; allow subsequent valid rows with same ticker to also be attempted/skipped appropriately
                continue

        return {
            "status": "ok",
            "received": int(received),
            "attempted": int(attempted),
            "added": {
                "count": len(added_tickers),
                "tickers": sorted(added_tickers)
            },
            "skipped": {
                "count": len(skipped_tickers),
                "tickers": sorted(skipped_tickers)
            },
            "failed": {
                "count": len(failed_tickers),
                "tickers": sorted(failed_tickers)
            },
            "legacy_counts": {
                "added": int(added),
                "skipped_existing": int(skipped_existing),
                "skipped_duplicate_in_request": int(skipped_duplicate_in_request),
                "skipped_invalid": int(skipped_invalid),
                "errors": int(errors)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        # Return error as a status object
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


# Upload CSV and reuse the bulk save to persist
# Expected headers (case-insensitive): ticker, name, company_name, [security_currency], [is_private]
@router.post("/bulk-csv")
async def upload_securities_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        # Decode and handle potential BOM
        text = content_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        # Normalize headers
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"ticker", "name", "company_name"}
        if not required.issubset(set(headers)):
            missing = ", ".join(sorted(required - set(headers)))
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {missing}")

        def parse_bool(v: str) -> bool:
            if v is None:
                return False
            s = str(v).strip().lower()
            return s in {"1", "true", "yes", "y"}

        # Build existing ticker set (case-insensitive)
        try:
            existing_tickers = { (s.ticker or "").strip().lower() for s in security_crud.list_all() }
        except Exception:
            existing_tickers = set()

        seen_in_request: set[str] = set()
        received = 0
        attempted = 0
        added = 0
        skipped_existing = 0
        skipped_duplicate_in_request = 0
        skipped_invalid = 0
        errors = 0
        
        # Track ticker lists for summary
        added_tickers = []
        skipped_tickers = []
        failed_tickers = []

        row_num = 1  # header is row 1, start counting data at 2 for clarity
        for row in reader:
            row_num += 1
            received += 1
            
            # Safely fetch with normalization
            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()

            ticker = get_val("ticker")
            name = get_val("name")
            company_name = get_val("company_name")
            currency = get_val("security_currency") or "USD"
            is_private_val = row.get("is_private") or row.get("IS_PRIVATE") or row.get("Is_Private")
            is_private = parse_bool(is_private_val)

            if not ticker or not name or not company_name:
                skipped_invalid += 1
                if ticker:  # Only add to skipped list if we have a ticker
                    skipped_tickers.append(ticker)
                continue

            key = ticker.lower()
            if key in seen_in_request:
                skipped_duplicate_in_request += 1
                skipped_tickers.append(ticker)
                continue

            attempted += 1
            try:
                norm = SecurityDtlInput(
                    ticker=ticker,
                    name=name,
                    company_name=company_name,
                    security_currency=currency,
                    is_private=is_private,
                )
                # Use upsert logic to update existing securities or create new ones
                if key in existing_tickers:
                    security_crud.update_by_ticker(ticker, norm)
                    skipped_existing += 1
                    skipped_tickers.append(ticker)
                else:
                    security_crud.save(norm)
                    existing_tickers.add(key)
                    added += 1
                    added_tickers.append(ticker)
                seen_in_request.add(key)
            except Exception:
                errors += 1
                failed_tickers.append(ticker)
                continue

        return {
            "status": "ok",
            "received": int(received),
            "attempted": int(attempted),
            "added": {
                "count": len(added_tickers),
                "tickers": sorted(added_tickers)
            },
            "skipped": {
                "count": len(skipped_tickers),
                "tickers": sorted(skipped_tickers)
            },
            "failed": {
                "count": len(failed_tickers),
                "tickers": sorted(failed_tickers)
            },
            "legacy_counts": {
                "added": int(added),
                "skipped_existing": int(skipped_existing),
                "skipped_duplicate_in_request": int(skipped_duplicate_in_request),
                "skipped_invalid": int(skipped_invalid),
                "errors": int(errors)
            }
        }

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

@router.get("", response_model=list[SecurityDtl])
@router.get("/", response_model=list[SecurityDtl])
def list_securities():
    return security_crud.list_all()

# CSV export endpoint
@router.get("/export.csv")
def export_securities_csv() -> Response:
    items = security_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)

    # Define CSV header and rows
    header = ["security_id", "ticker", "name", "company_name", "security_currency", "created_ts", "last_updated_ts"]
    writer.writerow(header)
    for s in items:
        writer.writerow([
            getattr(s, "security_id", ""),
            getattr(s, "ticker", ""),
            getattr(s, "name", ""),
            getattr(s, "company_name", ""),
            getattr(s, "security_currency", ""),
            getattr(s, "created_ts", ""),
            getattr(s, "last_updated_ts", ""),
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="securities.csv"'}
    )


@router.get("/{security_id}", response_model=SecurityDtl)
def get_security(security_id: int):
    s = security_crud.get_security(security_id)
    if not s:
        raise HTTPException(status_code=404, detail="Security not found")
    return s


@router.put("/{security_id}", response_model=SecurityDtl)
def update_security(security_id: int, security: SecurityDtlInput):
    try:
        return security_crud.update(security_id, security)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="Security not found")


@router.delete("/{security_id}", response_model=dict)
def delete_security(security_id: int):
    if not security_crud.delete(security_id):
        raise HTTPException(status_code=404, detail="Security not found")
    return {"deleted": True}


# Bulk-unique save: add multiple securities at once, skipping existing tickers
@router.post("/bulk-unique")
def save_securities_bulk_unique(securities: list[SecurityDtlInput]) -> dict:
    """
    Bulk create securities while skipping duplicates based on ticker (case-insensitive).
    Returns a summary with added items and skipped ones with reasons.
    """
    if not securities:
        return {"added": [], "skipped": []}

    # Build existing ticker set (case-insensitive)
    try:
        existing_tickers = { (s.ticker or "").strip().lower() for s in security_crud.list_all() }
    except Exception:
        existing_tickers = set()

    added: list[SecurityDtl] = []
    skipped: list[dict] = []
    seen_in_request: set[str] = set()

    for it in securities:
        try:
            ticker = (it.ticker or "").strip()
            name = (it.name or "").strip()
            company_name = (it.company_name or "").strip()
            currency = ((it.security_currency or "USD").strip() or "USD").upper()
            is_private = bool(getattr(it, "is_private", False))

            if not ticker or not name or not company_name:
                skipped.append({"input": it.model_dump(), "reason": "missing required fields"})
                continue

            key = ticker.lower()
            if key in existing_tickers:
                skipped.append({"input": it.model_dump(), "reason": "ticker already exists"})
                continue
            if key in seen_in_request:
                skipped.append({"input": it.model_dump(), "reason": "duplicate ticker in request"})
                continue

            norm = SecurityDtlInput(
                ticker=ticker,
                name=name,
                company_name=company_name,
                security_currency=currency,
                is_private=is_private,
            )
            saved = security_crud.save(norm)
            added.append(saved)
            seen_in_request.add(key)
            existing_tickers.add(key)
        except Exception as e:
            skipped.append({"input": it.model_dump() if hasattr(it, "model_dump") else str(it), "reason": str(e)})

    return {"added": added, "skipped": skipped}

# add an end point to pull company data using security_data_by_yahooquery for a list of tickers given and save the data into security_dtl
@router.post("/save_company_data_from_tickers")
def save_company_data_from_tickers(tickers: list[str] = []):
    # asset_profile_data = security_data_by_yahooquery.get_security_data(tickers, "asset_profile")
    price_data = security_data_by_yahooquery.get_security_data(tickers)
    price_data = price_data["price"]
    # build security_dtl objects and save/update them
    security_dtl_list = []
    for ticker, company_data in price_data.items():
        security_dtl = SecurityDtl(
            security_id=domain_utils.get_timestamp_with_microseconds(),
            ticker=ticker,
            name=company_data["shortName"],
            company_name=company_data["longName"],
            security_currency=company_data["currency"],
            is_private=False,
        )
        security_dtl_list.append(security_dtl)

    # save security_dtl objects as a bulk operation
    security_crud.save_many_with_upsert(security_dtl_list)
    return security_dtl_list
