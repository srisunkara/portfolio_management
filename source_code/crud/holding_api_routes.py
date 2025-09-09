# source_code/crud/holding_api_routes.py
import csv
import io
import datetime

from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import Response

from source_code.crud.holding_crud_operations import holding_crud
from source_code.models.models import HoldingDtl, HoldingDtlInput
from source_code.utils import domain_utils

router = APIRouter(prefix="/holdings", tags=["Holdings"])


@router.get("/", response_model=list[HoldingDtl])
def list_holdings():
    return holding_crud.list_holdings()


@router.get("/{holding_id}", response_model=HoldingDtl)
def get_holding(holding_id: int):
    h = holding_crud.get_security(holding_id)
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    return h


# Save single (server generates ID/timestamps)
@router.post("/", response_model=HoldingDtl)
def save_holding(holding: HoldingDtlInput):
    return holding_crud.save(holding)


# Bulk save JSON array of HoldingDtlInput
@router.post("/bulk", response_model=list[HoldingDtl])
def save_holdings_bulk(holdings: list[HoldingDtlInput]):
    if not holdings:
        return []
    return holding_crud.save_many(holdings)


# Upload CSV and reuse the bulk save to persist
# Expected headers (case-insensitive): holding_dt, portfolio_id, security_id, quantity, price, market_value
@router.post("/bulk-csv", response_model=list[HoldingDtl])
async def upload_holdings_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"portfolio_id", "security_id", "quantity", "price", "market_value"}
        missing = required - set(headers)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")

        items: list[HoldingDtlInput] = []
        row_num = 1
        for row in reader:
            row_num += 1

            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()

            holding_dt = get_val("holding_dt") or None  # optional, defaults server-side if omitted
            portfolio_id = get_val("portfolio_id")
            security_id = get_val("security_id")
            quantity = get_val("quantity")
            price = get_val("price")
            market_value = get_val("market_value")

            holding_dt = domain_utils.convert_to_date(holding_dt, datetime.date.today())

            # Basic validations and coercions
            try:
                portfolio_id = int(portfolio_id)
                security_id = int(security_id)
                quantity = float(quantity)
                price = float(price)
                market_value = float(market_value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: numeric fields are invalid")

            items.append(HoldingDtlInput(
                holding_dt=holding_dt,
                portfolio_id=portfolio_id,
                security_id=security_id,
                quantity=quantity,
                price=price,
                market_value=market_value,
            ))

        if not items:
            return []
        return holding_crud.save_many(items)
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


# CSV export endpoint
@router.get("/export.csv")
def export_holdings_csv() -> Response:
    items = holding_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)

    header = ["holding_id", "holding_dt", "portfolio_id", "security_id", "quantity", "price", "market_value",
              "created_ts", "last_updated_ts"]
    writer.writerow(header)
    for h in items:
        writer.writerow([
            getattr(h, "holding_id", ""),
            getattr(h, "holding_dt", ""),
            getattr(h, "portfolio_id", ""),
            getattr(h, "security_id", ""),
            getattr(h, "quantity", ""),
            getattr(h, "price", ""),
            getattr(h, "market_value", ""),
            getattr(h, "created_ts", ""),
            getattr(h, "last_updated_ts", ""),
        ])

    csv_data = output.getvalue()
    output.close()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="holdings.csv"'}
    )


@router.put("/{holding_id}", response_model=HoldingDtl)
def update_holding(holding_id: int, holding: HoldingDtlInput):
    try:
        return holding_crud.update(holding_id, holding)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="Holding not found")


@router.delete("/{holding_id}", response_model=dict)
def delete_holding(holding_id: int):
    if not holding_crud.delete(holding_id):
        raise HTTPException(status_code=404, detail="Holding not found")
    return {"deleted": True}
