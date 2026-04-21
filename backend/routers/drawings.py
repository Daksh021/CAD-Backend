import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Drawing, Balloon
from schemas.drawing_schema import DrawingResponse, DrawingDetail
from services.pdf_service import get_page_count, render_page_to_png
from services.detection_service import auto_detect_balloons

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=DrawingResponse)
async def upload_drawing(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path   = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(await file.read())

    page_count = get_page_count(str(file_path), file.content_type)

    drawing = Drawing(
        filename=unique_name,
        original_name=file.filename,
        file_path=str(file_path),
        page_count=page_count,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return drawing


@router.post("/upload-and-detect")
async def upload_and_detect(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Unified endpoint: upload a file (image or PDF), save it, run OCR auto-detection,
    and return the drawing record + detected balloons + rendered image URL.
    For PDFs, pages are converted to PNG images before OCR.
    """
    allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    # 1. Save the file
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path   = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 2. Determine page count
    page_count = get_page_count(str(file_path), file.content_type)

    # 3. Create drawing record
    drawing = Drawing(
        filename=unique_name,
        original_name=file.filename,
        file_path=str(file_path),
        page_count=page_count,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)

    # 4. Render page 1 to PNG (handles both PDF and image)
    #    This ensures we always have a PNG the frontend can display
    png_path = render_page_to_png(str(file_path), page=1)

    # 5. Run OCR auto-detection on page 1
    detections = auto_detect_balloons(str(file_path), page_number=1)

    # 6. Save detected balloons to DB
    created_balloons = []
    for idx, det in enumerate(detections, start=1):
        b = Balloon(
            drawing_id=drawing.id,
            balloon_number=idx,
            page_number=1,
            x_pct=float(det["x_pct"]),
            y_pct=float(det["y_pct"]),
            balloon_type=det["type"],
            extracted_text=str(det.get("text") or ""),
            description=str(det.get("description") or ""),
            is_auto=1,
        )
        db.add(b)
        created_balloons.append(b)

    db.commit()
    for b in created_balloons:
        db.refresh(b)

    # 7. Build the render URL for the frontend
    image_url = f"/api/drawings/{drawing.id}/render/1"

    return {
        "drawing": {
            "id": drawing.id,
            "filename": drawing.filename,
            "original_name": drawing.original_name,
            "file_path": drawing.file_path,
            "page_count": drawing.page_count,
        },
        "image_url": image_url,
        "detected_count": len(created_balloons),
        "balloons": [
            {
                "id": b.id,
                "drawing_id": b.drawing_id,
                "balloon_number": b.balloon_number,
                "page_number": b.page_number,
                "x_pct": b.x_pct,
                "y_pct": b.y_pct,
                "balloon_type": b.balloon_type.value if hasattr(b.balloon_type, "value") else str(b.balloon_type),
                "extracted_text": b.extracted_text,
                "description": b.description,
                "remarks": b.remarks,
                "is_auto": b.is_auto,
            }
            for b in created_balloons
        ],
    }


@router.get("/", response_model=list[DrawingResponse])
def list_drawings(db: Session = Depends(get_db)):
    return db.query(Drawing).all()


@router.get("/{drawing_id}", response_model=DrawingDetail)
def get_drawing(drawing_id: int, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return drawing


@router.get("/{drawing_id}/render/{page}")
def render_drawing(drawing_id: int, page: int = 1, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    png_path = render_page_to_png(drawing.file_path, page)
    return FileResponse(png_path, media_type="image/png")


@router.delete("/{drawing_id}")
def delete_drawing(drawing_id: int, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    db.delete(drawing)
    db.commit()
    return {"message": "Drawing deleted"}