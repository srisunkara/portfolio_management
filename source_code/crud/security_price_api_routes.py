# source_code/crud/security_price_api_routes.py
from datetime import datetime, date

from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
import csv
import io
from fastapi.responses import Response

from source_code.crud.security_price_crud_operations import security_price_crud
from source_code.models.models import SecurityPriceDtl, SecurityPriceDtlInput

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
