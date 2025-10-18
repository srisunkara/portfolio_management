# source_code/crud/portfolio_api.py
import csv
import datetime
import io

from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import Response

from source_code.crud.portfolio_crud_operations import portfolio_crud
from source_code.models.models import PortfolioDtl, PortfolioDtlInput
from source_code.utils import domain_utils

router = APIRouter(prefix="/api/portfolios", tags=["Portfolios"])


@router.post("/", response_model=PortfolioDtl)
def save_portfolio(portfolio: PortfolioDtlInput):
    return portfolio_crud.save(portfolio)


@router.post("/bulk", response_model=list[PortfolioDtl])
def save_portfolios_bulk(portfolios: list[PortfolioDtlInput]):
    if not portfolios:
        return []
    return portfolio_crud.save_many(portfolios)


# Upload CSV and reuse the bulk save to persist
# Expected headers (case-insensitive): user_id, name, [open_date], [close_date]
@router.post("/bulk-csv", response_model=list[PortfolioDtl])
async def upload_portfolios_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        text = content_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"user_id", "name"}
        missing = required - set(headers)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")

        items: list[PortfolioDtlInput] = []
        row_num = 1
        for row in reader:
            row_num += 1

            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()

            user_id = get_val("user_id")
            name = get_val("name")
            open_date = get_val("open_date") or None
            close_date = get_val("close_date") or None

            open_date = domain_utils.convert_to_date(open_date, datetime.date.today())

            if not user_id or not name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Row {row_num}: 'user_id' and 'name' are required"
                )

            try:
                user_id_num = int(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: 'user_id' must be an integer")

            items.append(PortfolioDtlInput(
                user_id=user_id_num,
                name=name,
                open_date=open_date,
                close_date=close_date
            ))

        if not items:
            return []

        return portfolio_crud.save_many(items)

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


@router.get("/", response_model=list[PortfolioDtl])
def list_portfolios():
    return portfolio_crud.list_all()


# CSV export endpoint
@router.get("/export.csv")
def export_portfolios_csv() -> Response:
    items = portfolio_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)

    header = ["portfolio_id", "user_id", "name", "open_date", "close_date", "created_ts", "last_updated_ts"]
    writer.writerow(header)
    for p in items:
        writer.writerow([
            getattr(p, "portfolio_id", ""),
            getattr(p, "user_id", ""),
            getattr(p, "name", ""),
            getattr(p, "open_date", ""),
            getattr(p, "close_date", ""),
            getattr(p, "created_ts", ""),
            getattr(p, "last_updated_ts", ""),
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="portfolios.csv"'}
    )


@router.get("/{portfolio_id}", response_model=PortfolioDtl)
def get_portfolio(portfolio_id: int):
    p = portfolio_crud.get_security(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p


@router.put("/{portfolio_id}", response_model=PortfolioDtl)
def update_portfolio(portfolio_id: int, portfolio: PortfolioDtlInput):
    try:
        return portfolio_crud.update(portfolio_id, portfolio)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="Portfolio not found")


@router.delete("/{portfolio_id}", response_model=dict)
def delete_portfolio(portfolio_id: int):
    if not portfolio_crud.delete(portfolio_id):
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"deleted": True}
