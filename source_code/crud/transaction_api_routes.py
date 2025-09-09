# source_code/crud/transaction_api.py
from fastapi import APIRouter, HTTPException

from source_code.crud.transaction_crud_operations import transaction_crud
from source_code.models.models import TransactionDtl, TransactionDtlInput, TransactionFullView

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionDtl)
def save_transaction(transaction: TransactionDtlInput):
    return transaction_crud.save(transaction)


@router.get("/", response_model=list[TransactionFullView])
def list_transactions_full():
    return transaction_crud.list_full()

# Bulk save JSON array
@router.post("/bulk", response_model=list[TransactionDtl])
def save_transactions_bulk(txns: list[TransactionDtlInput]):
    if not txns:
        return []
    return transaction_crud.save_many(txns)


@router.get("/{transaction_id}", response_model=TransactionDtl)
def get_transaction(transaction_id: int):
    t = transaction_crud.get_security(transaction_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return t


@router.put("/{transaction_id}", response_model=TransactionDtl)
def update_transaction(transaction_id: int, transaction: TransactionDtlInput):
    try:
        return transaction_crud.update(transaction_id, transaction)
    except ValueError as ve:
        # Body ID is not required; ValueError unlikely, keep for other validations
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="Transaction not found")


@router.delete("/{transaction_id}", response_model=dict)
def delete_transaction(transaction_id: int):
    if not transaction_crud.delete(transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"deleted": True}

# CSV upload and export
from fastapi import UploadFile, File
import csv, io
from fastapi.responses import Response

# Expected headers (case-insensitive): portfolio_id, security_id, external_platform_id, transaction_date, transaction_type, transaction_qty, transaction_price, [fees...]
@router.post("/bulk-csv", response_model=list[TransactionDtl])
async def upload_transactions_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    required = {"portfolio_id", "security_id", "external_platform_id", "transaction_date", "transaction_type", "transaction_qty", "transaction_price"}
    missing = required - set(headers)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")
    items: list[TransactionDtlInput] = []
    row_num = 1
    from datetime import datetime as dt, date
    for row in reader:
        row_num += 1
        def get_val(k: str) -> str:
            return (row.get(k) or row.get(k.upper()) or row.get(k.title()) or "").strip()
        try:
            portfolio_id = int(get_val("portfolio_id"))
            security_id = int(get_val("security_id"))
            external_platform_id = int(get_val("external_platform_id"))
            qty = float(get_val("transaction_qty"))
            price = float(get_val("transaction_price"))
            tdate_str = get_val("transaction_date")
            tdate = dt.strptime(tdate_str, "%Y-%m-%d").date() if tdate_str else date.today()
            ttype = get_val("transaction_type")
            if not ttype:
                raise ValueError("transaction_type required")
            # Optional fees
            def fnum(k, default=0.0):
                v = get_val(k)
                return float(v) if v else default
            items.append(TransactionDtlInput(
                portfolio_id=portfolio_id,
                security_id=security_id,
                external_platform_id=external_platform_id,
                transaction_date=tdate,
                transaction_type=ttype,
                transaction_qty=qty,
                transaction_price=price,
                transaction_fee=fnum("transaction_fee"),
                transaction_fee_percent=fnum("transaction_fee_percent"),
                carry_fee=fnum("carry_fee"),
                carry_fee_percent=fnum("carry_fee_percent"),
                management_fee=fnum("management_fee"),
                management_fee_percent=fnum("management_fee_percent"),
                external_manager_fee=fnum("external_manager_fee"),
                external_manager_fee_percent=fnum("external_manager_fee_percent"),
            ))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Row {row_num}: invalid value(s)")
    if not items:
        return []
    return transaction_crud.save_many(items)


@router.get("/export.csv")
def export_transactions_csv() -> Response:
    items = transaction_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)
    header = [
        "transaction_id","portfolio_id","security_id","external_platform_id","transaction_date","transaction_type",
        "transaction_qty","transaction_price","transaction_fee","transaction_fee_percent","carry_fee","carry_fee_percent",
        "management_fee","management_fee_percent","external_manager_fee","external_manager_fee_percent","created_ts","last_updated_ts"
    ]
    writer.writerow(header)
    for t in items:
        writer.writerow([
            getattr(t, "transaction_id", ""), getattr(t, "portfolio_id", ""), getattr(t, "security_id", ""), getattr(t, "external_platform_id", ""),
            getattr(t, "transaction_date", ""), getattr(t, "transaction_type", ""), getattr(t, "transaction_qty", ""), getattr(t, "transaction_price", ""),
            getattr(t, "transaction_fee", ""), getattr(t, "transaction_fee_percent", ""), getattr(t, "carry_fee", ""), getattr(t, "carry_fee_percent", ""),
            getattr(t, "management_fee", ""), getattr(t, "management_fee_percent", ""), getattr(t, "external_manager_fee", ""), getattr(t, "external_manager_fee_percent", ""),
            getattr(t, "created_ts", ""), getattr(t, "last_updated_ts", ""),
        ])
    csv_data = output.getvalue()
    output.close()
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="transactions.csv"'})
