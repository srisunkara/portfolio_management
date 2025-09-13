import csv
import io
from datetime import date
from datetime import datetime as dt, date as _date
from typing import Any

from fastapi import APIRouter, HTTPException
# CSV upload and export
from fastapi import UploadFile, File
from fastapi.responses import Response
# New: Bulk load by names (portfolio_name, security_ticker, external_platform_name)
from pydantic import BaseModel

from source_code.crud.external_platform_crud_operations import external_platform_crud
from source_code.crud.portfolio_crud_operations import portfolio_crud
from source_code.crud.security_crud_operations import security_crud
from source_code.crud.transaction_crud_operations import transaction_crud
from source_code.models.models import TransactionDtl, TransactionDtlInput, TransactionFullView, TransactionByNameInput

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionDtl)
def save_transaction(transaction: TransactionDtlInput):
    return transaction_crud.save(transaction)


@router.get("/", response_model=list[TransactionFullView])
def list_transactions_full():
    return transaction_crud.list_full()


@router.get("/form-data")
def get_transaction_form_data() -> dict[str, Any]:
    """
    Consolidated, lightweight payload for Add/Edit Transaction form to reduce
    number of client round-trips and payload size.
    Returns slim lists for portfolios, securities, and external platforms.
    If any underlying lookup fails (e.g., DB unavailable), return empty lists
    so the UI can still render the form instead of failing hard.
    """
    try:
        portfolios = [
            {"portfolio_id": p.portfolio_id, "name": p.name}
            for p in portfolio_crud.list_all()
        ]
    except Exception:
        portfolios = []
    try:
        securities = [
            {"security_id": s.security_id, "ticker": s.ticker, "name": s.name}
            for s in security_crud.list_all()
        ]
    except Exception:
        securities = []
    try:
        platforms = [
            {"external_platform_id": e.external_platform_id, "name": e.name}
            for e in external_platform_crud.list_all()
        ]
    except Exception:
        platforms = []

    return {
        "portfolios": portfolios,
        "securities": securities,
        "external_platforms": platforms,
    }


# Bulk save JSON array
@router.post("/bulk", response_model=list[TransactionDtl])
def save_transactions_bulk(txns: list[TransactionDtlInput]):
    if not txns:
        return []
    return transaction_crud.save_many(txns)


@router.get("/{transaction_id}", response_model=TransactionDtl)
def get_transaction(transaction_id: int):
    t = transaction_crud.get_transaction(transaction_id)
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
    required = {"portfolio_id", "security_id", "external_platform_id", "transaction_date", "transaction_type",
                "transaction_qty", "transaction_price"}
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
        "transaction_id", "portfolio_id", "security_id", "external_platform_id", "transaction_date", "transaction_type",
        "transaction_qty", "transaction_price", "transaction_fee", "transaction_fee_percent", "carry_fee",
        "carry_fee_percent",
        "management_fee", "management_fee_percent", "external_manager_fee", "external_manager_fee_percent",
        "created_ts", "last_updated_ts"
    ]
    writer.writerow(header)
    for t in items:
        writer.writerow([
            getattr(t, "transaction_id", ""), getattr(t, "portfolio_id", ""), getattr(t, "security_id", ""),
            getattr(t, "external_platform_id", ""),
            getattr(t, "transaction_date", ""), getattr(t, "transaction_type", ""), getattr(t, "transaction_qty", ""),
            getattr(t, "transaction_price", ""),
            getattr(t, "transaction_fee", ""), getattr(t, "transaction_fee_percent", ""), getattr(t, "carry_fee", ""),
            getattr(t, "carry_fee_percent", ""),
            getattr(t, "management_fee", ""), getattr(t, "management_fee_percent", ""),
            getattr(t, "external_manager_fee", ""), getattr(t, "external_manager_fee_percent", ""),
            getattr(t, "created_ts", ""), getattr(t, "last_updated_ts", ""),
        ])
    csv_data = output.getvalue()
    output.close()
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="transactions.csv"'})


@router.post("/bulk-by-name")
def save_transactions_bulk_by_name(items: list[TransactionByNameInput]) -> dict[str, Any]:
    if not items:
        return {"loaded": [], "excluded": []}

    # Build lookup maps (case-insensitive)
    portfolio_map = {p.name.strip().lower(): p.portfolio_id for p in portfolio_crud.list_all()}
    security_map = {s.ticker.strip().lower(): s.security_id for s in security_crud.list_all()}
    platform_map = {e.name.strip().lower(): e.external_platform_id for e in external_platform_crud.list_all()}

    loaded: list[TransactionDtl] = []
    excluded: list[dict[str, Any]] = []

    for it in items:
        reasons: list[str] = []
        pid = portfolio_map.get(it.portfolio_name.strip().lower())
        if pid is None:
            reasons.append("portfolio not found")
        sid = security_map.get(it.security_ticker.strip().lower())
        if sid is None:
            reasons.append("security not found")
        eid = platform_map.get(it.external_platform_name.strip().lower())
        if eid is None:
            reasons.append("external platform not found")

        if reasons:
            excluded.append({
                "input": it.model_dump(),
                "reason": ", ".join(reasons),
            })
            continue

        # Create TransactionDtlInput with resolved IDs
        tx_input = TransactionDtlInput(
            portfolio_id=pid,
            security_id=sid,
            external_platform_id=eid,
            transaction_date=it.transaction_date,
            transaction_type=it.transaction_type,
            transaction_qty=it.transaction_qty,
            transaction_price=it.transaction_price,
            transaction_fee=it.transaction_fee,
            transaction_fee_percent=it.transaction_fee_percent,
            carry_fee=it.carry_fee,
            carry_fee_percent=it.carry_fee_percent,
            management_fee=it.management_fee,
            management_fee_percent=it.management_fee_percent,
            external_manager_fee=it.external_manager_fee,
            external_manager_fee_percent=it.external_manager_fee_percent,
        )
        loaded.append(transaction_crud.save(tx_input))

    return {"loaded": loaded, "excluded": excluded}


# New: Upload CSV using names (portfolio_name, security_ticker, external_platform_name)
@router.post("/bulk-by-name-csv")
async def upload_transactions_by_name_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    required = {
        "portfolio_name", "security_ticker", "external_platform_name",
        "transaction_date", "transaction_type", "transaction_qty", "transaction_price"
    }
    missing = required - set(headers)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")

    # Build lookup maps (case-insensitive)
    portfolio_map = {p.name.strip().lower(): p.portfolio_id for p in portfolio_crud.list_all()}
    security_map = {s.ticker.strip().lower(): s.security_id for s in security_crud.list_all()}
    platform_map = {e.name.strip().lower(): e.external_platform_id for e in external_platform_crud.list_all()}

    loaded: list[TransactionDtl] = []
    excluded: list[dict[str, Any]] = []

    row_num = 1
    for row in reader:
        row_num += 1

        def get_val(k: str) -> str:
            return (row.get(k) or row.get(k.upper()) or row.get(k.title()) or "").strip()

        def fnum(k: str, default=0.0) -> float:
            v = get_val(k)
            return float(v) if v else default

        try:
            portfolio_name = get_val("portfolio_name")
            security_ticker = get_val("security_ticker")
            external_platform_name = get_val("external_platform_name")
            ttype = get_val("transaction_type")
            if not (portfolio_name and security_ticker and external_platform_name and ttype):
                raise ValueError("Missing required fields")

            qty = float(get_val("transaction_qty"))
            price = float(get_val("transaction_price"))
            tdate_str = get_val("transaction_date")
            tdate = dt.strptime(tdate_str, "%Y-%m-%d").date() if tdate_str else _date.today()
        except ValueError:
            excluded.append({
                "input": {k: row.get(k) for k in row.keys()},
                "reason": f"Row {row_num}: invalid or missing required value(s)"
            })
            continue

        reasons: list[str] = []
        pid = portfolio_map.get(portfolio_name.strip().lower())
        if pid is None:
            reasons.append("portfolio not found")
        sid = security_map.get(security_ticker.strip().lower())
        if sid is None:
            reasons.append("security not found")
        eid = platform_map.get(external_platform_name.strip().lower())
        if eid is None:
            reasons.append("external platform not found")

        if reasons:
            excluded.append({
                "input": {
                    "portfolio_name": portfolio_name,
                    "security_ticker": security_ticker,
                    "external_platform_name": external_platform_name,
                    "transaction_date": tdate.isoformat(),
                    "transaction_type": ttype,
                    "transaction_qty": qty,
                    "transaction_price": price,
                    "transaction_fee": fnum("transaction_fee"),
                    "transaction_fee_percent": fnum("transaction_fee_percent"),
                    "carry_fee": fnum("carry_fee"),
                    "carry_fee_percent": fnum("carry_fee_percent"),
                    "management_fee": fnum("management_fee"),
                    "management_fee_percent": fnum("management_fee_percent"),
                    "external_manager_fee": fnum("external_manager_fee"),
                    "external_manager_fee_percent": fnum("external_manager_fee_percent"),
                },
                "reason": ", ".join(reasons),
            })
            continue

        tx_input = TransactionDtlInput(
            portfolio_id=pid,
            security_id=sid,
            external_platform_id=eid,
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
        )
        loaded.append(transaction_crud.save(tx_input))

    return {"loaded": loaded, "excluded": excluded}



