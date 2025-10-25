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

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionDtl)
def save_transaction(transaction: TransactionDtlInput):
    return transaction_crud.save(transaction)


@router.get("", response_model=list[TransactionFullView])
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
            {"portfolio_id": p.portfolio_id, "user_id": p.user_id, "name": p.name}
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

    from source_code.models.models import TRANSACTION_TYPES

    return {
        "portfolios": portfolios,
        "securities": securities,
        "external_platforms": platforms,
        "transaction_types": [{"code": k, "label": v} for k, v in TRANSACTION_TYPES.items()],
    }


# Get linked transaction pairs for performance comparison
@router.get("/linked-pairs")
def get_linked_transaction_pairs(user_id: int | None = None):
    """Get linked transaction pairs; when user_id provided, limit to that user's portfolios."""
    try:
        all_transactions = transaction_crud.list_full()
        # Optional filter by user_id if TransactionFullView includes user_id
        if user_id is not None:
            all_transactions = [t for t in all_transactions if getattr(t, "user_id", None) == user_id]
        
        # Find transactions that have duplicates (rel_transaction_id is not None)
        duplicate_transactions = [t for t in all_transactions if t.rel_transaction_id is not None]
        
        # Build pairs: original transaction and its duplicate
        pairs = []
        for duplicate in duplicate_transactions:
            original = next((t for t in all_transactions if t.transaction_id == duplicate.rel_transaction_id), None)
            if original:
                pairs.append({
                    "pair_id": f"{original.transaction_id}-{duplicate.transaction_id}",
                    "original": {
                        "transaction_id": original.transaction_id,
                        "transaction_date": original.transaction_date.isoformat(),
                        "security_ticker": original.security_ticker,
                        "security_name": original.security_name,
                        "total_inv_amt": original.total_inv_amt,
                        "portfolio_name": original.portfolio_name,
                        "portfolio_id": original.portfolio_id,
                        "user_id": getattr(original, "user_id", None),
                    },
                    "duplicate": {
                        "transaction_id": duplicate.transaction_id,
                        "transaction_date": duplicate.transaction_date.isoformat(),
                        "security_ticker": duplicate.security_ticker,
                        "security_name": duplicate.security_name,
                        "total_inv_amt": duplicate.total_inv_amt,
                        "portfolio_name": duplicate.portfolio_name,
                        "portfolio_id": duplicate.portfolio_id,
                        "user_id": getattr(duplicate, "user_id", None),
                    }
                })
        
        return {"pairs": pairs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get performance data for a specific linked transaction pair
@router.get("/performance-comparison/{pair_id}")
def get_performance_comparison(pair_id: str, from_date: date, to_date: date):
    """Get performance data for a linked transaction pair over a date range"""
    try:
        # Parse pair_id to get original and duplicate transaction IDs
        parts = pair_id.split("-")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid pair_id format")
        
        original_id = int(parts[0])
        duplicate_id = int(parts[1])
        
        # Get the transactions
        all_transactions = transaction_crud.list_full()
        original = transaction_crud.get_transaction_by_id(original_id)
        duplicate = transaction_crud.get_transaction_by_id(duplicate_id)

        # original = next((t for t in all_transactions if t.transaction_id == original_id), None)
        # duplicate = next((t for t in all_transactions if t.transaction_id == duplicate_id), None)
        
        if not original or not duplicate:
            raise HTTPException(status_code=404, detail="Transaction pair not found")
        
        # Import security price operations
        from source_code.crud.security_price_crud_operations import security_price_crud
        
        # Get price data for both securities over the date range
        original_prices = security_price_crud.list_by_date_range_and_ticker(
            from_date=from_date, 
            to_date=to_date, 
            ticker=original.security_ticker
        )
        
        duplicate_prices = security_price_crud.list_by_date_range_and_ticker(
            from_date=from_date, 
            to_date=to_date, 
            ticker=duplicate.security_ticker
        )
        
        # Calculate investment performance data
        original_performance = []
        duplicate_performance = []
        
        # Use transaction prices as baseline for investment performance
        original_transaction_price = original.transaction_price
        duplicate_transaction_price = duplicate.transaction_price
        
        # Calculate quantities based on investment amounts
        original_qty = original.transaction_qty if original.transaction_qty else (original.total_inv_amt / original_transaction_price)
        duplicate_qty = duplicate.transaction_qty if duplicate.transaction_qty else (duplicate.total_inv_amt / duplicate_transaction_price)
        
        # Calculate daily investment performance relative to transaction price
        # Always use transaction price as baseline so performance starts at 0% on transaction date
        # This ensures the graph shows performance for the selected date range rather than from first price date
        original_baseline_value = original.total_inv_amt
        
        for price in original_prices:
            if original_transaction_price and original_qty and original_baseline_value:
                # Current value of the investment
                current_value = original_qty * price.price
                # Investment performance vs baseline value (not original investment amount)
                performance = ((current_value - original_baseline_value) / original_baseline_value) * 100
                # Unrealized gain/loss in dollars (vs original investment amount)
                unrealized_gain_loss = current_value - original.total_inv_amt
                
                original_performance.append({
                    "date": price.price_date.isoformat(),
                    "performance": round(performance, 2),
                    "price": price.price,
                    "current_value": round(current_value, 2),
                    "unrealized_gain_loss": round(unrealized_gain_loss, 2),
                    "unrealized_gain_loss_pct": round(((current_value - original.total_inv_amt) / original.total_inv_amt) * 100, 2)
                })
        
        # Calculate baseline for duplicate performance - always use transaction investment amount
        # This ensures consistent baseline logic for both original and duplicate transactions
        duplicate_baseline_value = duplicate.total_inv_amt
        
        for price in duplicate_prices:
            if duplicate_transaction_price and duplicate_qty and duplicate_baseline_value:
                # Current value of the investment
                current_value = duplicate_qty * price.price
                # Investment performance vs baseline value (not original investment amount)
                performance = ((current_value - duplicate_baseline_value) / duplicate_baseline_value) * 100
                # Unrealized gain/loss in dollars (vs original investment amount)
                unrealized_gain_loss = current_value - duplicate.total_inv_amt
                
                duplicate_performance.append({
                    "date": price.price_date.isoformat(),
                    "performance": round(performance, 2),
                    "price": price.price,
                    "current_value": round(current_value, 2),
                    "unrealized_gain_loss": round(unrealized_gain_loss, 2),
                    "unrealized_gain_loss_pct": round(((current_value - duplicate.total_inv_amt) / duplicate.total_inv_amt) * 100, 2)
                })
        
        # Get latest performance for summary
        latest_original_performance = original_performance[-1] if original_performance else None
        latest_duplicate_performance = duplicate_performance[-1] if duplicate_performance else None
        
        # Calculate total fees for each transaction
        original_total_fees = (
            (original.transaction_fee or 0) +
            (original.management_fee or 0) +
            (original.external_manager_fee or 0) +
            (original.carry_fee or 0)
        )
        
        duplicate_total_fees = (
            (duplicate.transaction_fee or 0) +
            (duplicate.management_fee or 0) +
            (duplicate.external_manager_fee or 0) +
            (duplicate.carry_fee or 0)
        )

        return {
            "pair_info": {
                "original": {
                    "security_ticker": original.security_ticker,
                    "security_name": original.security_name,
                    "transaction_date": original.transaction_date.isoformat(),
                    "total_inv_amt": original.total_inv_amt,
                    "transaction_price": original_transaction_price,
                    "quantity": round(original_qty, 4),
                    "total_fees_paid": round(original_total_fees, 2),
                    "current_value": latest_original_performance["current_value"] if latest_original_performance else None,
                    "unrealized_gain_loss": latest_original_performance["unrealized_gain_loss"] if latest_original_performance else None,
                    "unrealized_gain_loss_pct": latest_original_performance["unrealized_gain_loss_pct"] if latest_original_performance else None
                },
                "duplicate": {
                    "security_ticker": duplicate.security_ticker,
                    "security_name": duplicate.security_name,
                    "transaction_date": duplicate.transaction_date.isoformat(),
                    "total_inv_amt": duplicate.total_inv_amt,
                    "transaction_price": duplicate_transaction_price,
                    "quantity": round(duplicate_qty, 4),
                    "total_fees_paid": round(duplicate_total_fees, 2),
                    "current_value": latest_duplicate_performance["current_value"] if latest_duplicate_performance else None,
                    "unrealized_gain_loss": latest_duplicate_performance["unrealized_gain_loss"] if latest_duplicate_performance else None,
                    "unrealized_gain_loss_pct": latest_duplicate_performance["unrealized_gain_loss_pct"] if latest_duplicate_performance else None
                }
            },
            "performance_data": {
                "original": original_performance,
                "duplicate": duplicate_performance
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid pair_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


# Expected headers (case-insensitive): portfolio_id, security_id, external_platform_id, transaction_date, transaction_type, transaction_qty, transaction_price, [total_inv_amt], [fees...]
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

            # Optional total investment amount
            total_inv_amt_val = get_val("total_inv_amt")
            total_inv_amt = float(total_inv_amt_val) if total_inv_amt_val else (qty * price)

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
                total_inv_amt=total_inv_amt,
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
        "total_inv_amt",
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
            getattr(t, "total_inv_amt", ""),
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


# Recalculate fees based on percent fields for all transactions
@router.post("/recalculate-fees")
def recalculate_fees() -> dict[str, int]:
    try:
        updated = transaction_crud.recalculate_fees_all()
        return {"updated": int(updated)}
    except Exception as e:
        # surface a 500 with error message
        raise HTTPException(status_code=500, detail=str(e))
