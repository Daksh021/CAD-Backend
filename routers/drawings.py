import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Drawing
from schemas.drawing_schema import DrawingResponse, DrawingDetail
from services.pdf_service import get_page_count, render_page_to_png

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