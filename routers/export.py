import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Balloon, Drawing
from schemas.export_schema import ExportRequest
from services.excel_service import build_excel_workbook

router = APIRouter()


@router.post("/excel")
def export_excel(req: ExportRequest, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == req.drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    balloons = (
        db.query(Balloon)
        .filter(Balloon.drawing_id == req.drawing_id)
        .order_by(Balloon.page_number, Balloon.balloon_number)
        .all()
    )

    if not balloons:
        raise HTTPException(status_code=404, detail="No balloons found")

    wb     = build_excel_workbook(drawing, balloons, include_remarks=req.include_remarks)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"balloons_{drawing.original_name.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )