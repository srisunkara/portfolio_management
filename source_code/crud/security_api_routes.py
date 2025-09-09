# source_code/crud/security_api.py
from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
import csv
import io
from fastapi.responses import Response

from source_code.crud.security_crud_operations import security_crud
from source_code.models.models import SecurityDtl, SecurityDtlInput

router = APIRouter(prefix="/securities", tags=["Securities"])


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

# Upload CSV and reuse the bulk save to persist
# Expected headers (case-insensitive): ticker, name, company_name, [security_currency]
@router.post("/bulk-csv", response_model=list[SecurityDtl])
async def upload_securities_csv(file: UploadFile = File(...)):
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

        items: list[SecurityDtlInput] = []
        row_num = 1  # header is row 1, start counting data at 2 for clarity
        for row in reader:
            row_num += 1
            # Safely fetch with normalization
            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()

            ticker = get_val("ticker")
            name = get_val("name")
            company_name = get_val("company_name")
            currency = get_val("security_currency") or "USD"

            if not ticker or not name or not company_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Row {row_num}: 'ticker', 'name', and 'company_name' are required"
                )

            items.append(SecurityDtlInput(
                ticker=ticker,
                name=name,
                company_name=company_name,
                security_currency=currency
            ))

        if not items:
            return []

        # Reuse bulk persistence
        return security_crud.save_many(items)

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

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
