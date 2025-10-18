# source_code/crud/company_valuations_api_routes.py
import csv
import io
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from source_code.crud.company_valuations_crud_operations import company_valuation_crud
from source_code.models.models import CompanyValuationDtl, CompanyValuationDtlInput

router = APIRouter(prefix="/api/company-valuations", tags=["Company Valuations"])


@router.get("/", response_model=list[CompanyValuationDtl])
def list_company_valuations(date: date | None = None):
    """List all company valuations, optionally filtered by date."""
    if date is not None:
        return company_valuation_crud.list_by_date(date)
    return company_valuation_crud.list_all()


@router.get("/{company_id}", response_model=CompanyValuationDtl)
def get_company_valuation(company_id: int):
    """Get a specific company valuation by ID."""
    company = company_valuation_crud.get_security(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company valuation not found")
    return company


@router.post("/", response_model=CompanyValuationDtl)
def save_company_valuation(company: CompanyValuationDtlInput):
    """Create or update a company valuation record."""
    return company_valuation_crud.save(company)


@router.post("/bulk", response_model=list[CompanyValuationDtl])
def save_company_valuations_bulk(companies: list[CompanyValuationDtlInput]):
    """Bulk create/update company valuation records."""
    if not companies:
        return []
    return company_valuation_crud.save_many(companies)


@router.put("/{company_id}", response_model=CompanyValuationDtl)
def update_company_valuation(company_id: int, company: CompanyValuationDtlInput):
    """Update a company valuation record."""
    try:
        return company_valuation_crud.update(company_id, company)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="Company valuation not found")


@router.delete("/{company_id}", response_model=dict)
def delete_company_valuation(company_id: int):
    """Delete a company valuation record."""
    if not company_valuation_crud.delete(company_id):
        raise HTTPException(status_code=404, detail="Company valuation not found")
    return {"deleted": True}


# CSV export endpoint
@router.get("/export.csv")
def export_company_valuations_csv() -> Response:
    """Export company valuations to CSV."""
    items = company_valuation_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)

    header = [
        "company_valuation_id", "as_of_date", "price_source", "company", "sector_subsector",
        "price", "price_change_amt", "price_change_perc", "last_matched_price",
        "share_class", "post_money_valuation", "price_per_share", "amount_raised",
        "created_ts", "last_updated_ts"
    ]
    writer.writerow(header)
    
    for company in items:
        writer.writerow([
            getattr(company, "company_valuation_id", ""),
            getattr(company, "as_of_date", ""),
            getattr(company, "price_source", ""),
            getattr(company, "company", ""),
            getattr(company, "sector_subsector", ""),
            getattr(company, "price", ""),
            getattr(company, "price_change_amt", ""),
            getattr(company, "price_change_perc", ""),
            getattr(company, "last_matched_price", ""),
            getattr(company, "share_class", ""),
            getattr(company, "post_money_valuation", ""),
            getattr(company, "price_per_share", ""),
            getattr(company, "amount_raised", ""),
            getattr(company, "created_ts", ""),
            getattr(company, "last_updated_ts", ""),
        ])

    csv_data = output.getvalue()
    output.close()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="company_valuations.csv"'}
    )


# CSV upload endpoint
@router.post("/bulk-csv", response_model=list[CompanyValuationDtl])
async def upload_company_valuations_csv(file: UploadFile = File(...)):
    """Upload and process CSV file containing company valuation data."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        text = content_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"as_of_date", "company"}
        missing = required - set(headers)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")

        items: list[CompanyValuationDtlInput] = []
        row_num = 1
        for row in reader:
            row_num += 1

            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()

            def get_float(key: str) -> float | None:
                val = get_val(key)
                if not val:
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None

            try:
                as_of_date_str = get_val("as_of_date")
                if not as_of_date_str:
                    raise ValueError("as_of_date is required")
                
                from datetime import datetime
                as_of_date = datetime.strptime(as_of_date_str, "%Y-%m-%d").date()
                
                company_name = get_val("company")
                if not company_name:
                    raise ValueError("company name is required")

                items.append(CompanyValuationDtlInput(
                    as_of_date=as_of_date,
                    price_source=get_val("price_source") or "External",
                    company=company_name,
                    sector_subsector=get_val("sector_subsector"),
                    price=get_float("price"),
                    price_change_amt=get_float("price_change_amt"),
                    price_change_perc=get_float("price_change_perc"),
                    last_matched_price=get_val("last_matched_price"),
                    share_class=get_val("share_class"),
                    post_money_valuation=get_val("post_money_valuation"),
                    price_per_share=get_float("price_per_share"),
                    amount_raised=get_val("amount_raised"),
                ))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: {str(e)}")

        if not items:
            return []
        return company_valuation_crud.save_many(items)

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


# Data loader endpoints for ForgeGlobal CSV data
class ForgeDataLoaderRequest(BaseModel):
    csv_file_path: str
    as_of_date: Optional[date] = None
    price_source: str = "ForgeGlobal"


class ForgeAutoLoadRequest(BaseModel):
    price_source: str = "ForgeGlobal"


@router.post("/load-forge-file")
def load_forge_file(request: ForgeDataLoaderRequest) -> dict[str, Any]:
    """Load a specific ForgeGlobal CSV file into company valuations table using the advanced loader."""
    try:
        # Import the loader utility
        from source_code.utils.company_valuations_loader import CompanyValuationsLoader
        
        loader = CompanyValuationsLoader(price_source=request.price_source)
        result = loader.load_csv_file(request.csv_file_path, request.as_of_date)
        
        return {
            "status": "success",
            "loaded": result['loaded'],
            "skipped": result['skipped'], 
            "errors": result['errors'],
            "file": result['file'],
            "as_of_date": result['as_of_date'],
            "error_details": result['error_details'][:5] if result['error_details'] else []  # First 5 errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")


@router.post("/load-forge-auto")
def load_forge_auto_discover(request: ForgeAutoLoadRequest = None) -> dict[str, Any]:
    """Auto-discover and load all ForgeGlobal CSV files from the samples directory."""
    try:
        # Import the loader utility
        from source_code.utils.company_valuations_loader import CompanyValuationsLoader
        
        price_source = request.price_source if request else "ForgeGlobal"
        loader = CompanyValuationsLoader(price_source=price_source)
        results = loader.auto_discover_and_load()
        
        # Aggregate results
        total_loaded = sum(r.get('loaded', 0) for r in results)
        total_skipped = sum(r.get('skipped', 0) for r in results)
        total_errors = sum(r.get('errors', 0) for r in results)
        
        return {
            "status": "success",
            "files_processed": len(results),
            "total_loaded": total_loaded,
            "total_skipped": total_skipped,
            "total_errors": total_errors,
            "file_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-load data: {str(e)}")


@router.post("/load-forge-data")
def load_forge_data(request: ForgeDataLoaderRequest) -> dict[str, Any]:
    """Load ForgeGlobal CSV data into company valuations table (legacy endpoint)."""
    import os
    import re
    
    if not os.path.exists(request.csv_file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.csv_file_path}")

    try:
        items: list[CompanyValuationDtlInput] = []
        
        with open(request.csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    company_name = (row.get("Company") or "").strip()
                    if not company_name:
                        continue
                    
                    # Parse Forge Price (split composite field)
                    forge_price_raw = (row.get("Forge Price1") or row.get("Forge Price") or "").strip()
                    price = None
                    price_change_amt = None
                    price_change_perc = None
                    
                    if forge_price_raw and forge_price_raw != "--":
                        # Extract price (first number with optional $)
                        price_match = re.search(r"\$?([0-9,]+\.?\d*)", forge_price_raw)
                        if price_match:
                            price = float(price_match.group(1).replace(",", ""))
                        
                        # Extract change amount (signed number before %)
                        change_match = re.search(r"([+-]\$?[0-9,]+\.?\d*)\s*\(", forge_price_raw)
                        if change_match:
                            price_change_amt = float(change_match.group(1).replace("$", "").replace(",", ""))
                        
                        # Extract change percentage
                        perc_match = re.search(r"\(([+-]?[0-9.]+)%\)", forge_price_raw)
                        if perc_match:
                            price_change_perc = float(perc_match.group(1))
                    
                    # Parse price per share
                    price_per_share = None
                    price_per_share_str = (row.get("Price Per Share") or "").strip()
                    if price_per_share_str and price_per_share_str not in ["--", ""]:
                        try:
                            price_per_share = float(price_per_share_str.replace("$", "").replace(",", ""))
                        except ValueError:
                            pass

                    items.append(CompanyValuationDtlInput(
                        as_of_date=request.as_of_date if request.as_of_date else date.today(),
                        price_source=request.price_source,
                        company=company_name,
                        sector_subsector=(row.get("Sector & Subsector") or "").strip(),
                        price=price,
                        price_change_amt=price_change_amt,
                        price_change_perc=price_change_perc,
                        last_matched_price=(row.get("Last Matched Price") or "").strip(),
                        share_class=(row.get("Share Class") or "").strip(),
                        post_money_valuation=(row.get("Post-Money Valuation2") or row.get("Post-Money Valuation") or "").strip(),
                        price_per_share=price_per_share,
                        amount_raised=(row.get("Amount Raised") or "").strip(),
                        raw_data_json=dict(row),  # Store original row for reference
                    ))
                except Exception as e:
                    print(f"Warning: Skipping row {row_num} due to error: {e}")
                    continue

        if not items:
            return {"loaded": 0, "message": "No valid data found in CSV"}

        saved_items = company_valuation_crud.save_many(items)
        return {
            "loaded": len(saved_items),
            "file": request.csv_file_path,
            "as_of_date": (request.as_of_date if request.as_of_date else date.today()).isoformat(),
            "price_source": request.price_source
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")