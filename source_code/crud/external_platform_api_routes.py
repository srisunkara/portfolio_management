# source_code/crud/trading_platform_api.py
import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import Response

from source_code.crud.external_platform_crud_operations import external_platform_crud
from source_code.models.models import ExternalPlatformDtl, ExternalPlatformDtlInput, ALLOWED_PLATFORM_TYPES

router = APIRouter(prefix="/external-platforms", tags=["External Platforms"])


@router.post("/", response_model=ExternalPlatformDtl)
def save_platform(platform: ExternalPlatformDtlInput):
    # validate platform_type against allowed values
    if platform.platform_type not in ALLOWED_PLATFORM_TYPES:
        raise HTTPException(status_code=400, detail=f"platform_type must be one of {ALLOWED_PLATFORM_TYPES}")
    return external_platform_crud.save(platform)


@router.post("/bulk", response_model=list[ExternalPlatformDtl])
def save_platforms_bulk(platforms: list[ExternalPlatformDtlInput]):
    if not platforms:
        return []
    for p in platforms:
        if p.platform_type not in ALLOWED_PLATFORM_TYPES:
            raise HTTPException(status_code=400, detail=f"platform_type must be one of {ALLOWED_PLATFORM_TYPES}")
    return external_platform_crud.save_many(platforms)


@router.post("/bulk-csv", response_model=list[ExternalPlatformDtl])
async def upload_platforms_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Empty file")
        text = content_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        required = {"name", "platform_type"}
        missing = required - set(headers)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")
        items: list[ExternalPlatformDtlInput] = []
        row_num = 1
        for row in reader:
            row_num += 1
            def get_val(key: str) -> str:
                return (row.get(key) or row.get(key.upper()) or row.get(key.title()) or "").strip()
            name = get_val("name")
            ptype = get_val("platform_type")
            if not name:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: 'name' is required")
            if ptype not in ALLOWED_PLATFORM_TYPES:
                raise HTTPException(status_code=400, detail=f"Row {row_num}: platform_type must be one of {ALLOWED_PLATFORM_TYPES}")
            items.append(ExternalPlatformDtlInput(name=name, platform_type=ptype))
        if not items:
            return []
        return external_platform_crud.save_many(items)
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Use UTF-8 encoded CSV.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


@router.get("/", response_model=list[ExternalPlatformDtl])
def list_platforms():
    return external_platform_crud.list_all()


@router.get("/export.csv")
def export_platforms_csv() -> Response:
    items = external_platform_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["external_platform_id", "name", "platform_type", "created_ts", "last_updated_ts"]
    writer.writerow(header)
    for p in items:
        writer.writerow([
            getattr(p, "external_platform_id", ""),
            getattr(p, "name", ""),
            getattr(p, "platform_type", ""),
            getattr(p, "created_ts", ""),
            getattr(p, "last_updated_ts", ""),
        ])
    csv_data = output.getvalue()
    output.close()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="external_platforms.csv"'}
    )


@router.get("/{external_platform_id}", response_model=ExternalPlatformDtl)
def get_platform(external_platform_id: int):
    p = external_platform_crud.get_security(external_platform_id)
    if not p:
        raise HTTPException(status_code=404, detail="External platform not found")
    return p


@router.put("/{external_platform_id}", response_model=ExternalPlatformDtl)
def update_platform(external_platform_id: int, platform: ExternalPlatformDtlInput):
    try:
        return external_platform_crud.update(external_platform_id, platform)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="External platform not found")


@router.delete("/{external_platform_id}", response_model=dict)
def delete_platform(external_platform_id: int):
    if not external_platform_crud.delete(external_platform_id):
        raise HTTPException(status_code=404, detail="External platform not found")
    return {"deleted": True}
