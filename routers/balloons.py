import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Balloon, Drawing
from schemas import (
    BalloonCreate, BalloonUpdate, BalloonResponse,
    AutoDetectRequest, AutoDetectResponse,
)
from services.detection_service import auto_detect_balloons

router = APIRouter()


def _next_number(drawing_id: int, db: Session) -> int:
    existing = (
        db.query(Balloon)
        .filter(Balloon.drawing_id == drawing_id)
        .order_by(Balloon.balloon_number.desc())
        .first()
    )
    return (existing.balloon_number + 1) if existing else 1


@router.post("/auto-detect", response_model=AutoDetectResponse)
def run_auto_detection(req: AutoDetectRequest, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == req.drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    db.query(Balloon).filter(
        Balloon.drawing_id == req.drawing_id,
        Balloon.page_number == req.page_number,
        Balloon.is_auto == 1,
    ).delete()
    db.commit()

    detections = auto_detect_balloons(drawing.file_path, req.page_number)

    created = []
    for idx, det in enumerate(detections, start=1):
        b = Balloon(
            drawing_id=req.drawing_id,
            balloon_number=idx,
            page_number=req.page_number,
            x_pct=det["x_pct"],
            y_pct=det["y_pct"],
            balloon_type=det["type"],
            extracted_text=det.get("text"),
            description=det.get("description"),
            is_auto=1,
        )
        db.add(b)
        created.append(b)

    db.commit()
    for b in created:
        db.refresh(b)

    return AutoDetectResponse(
        drawing_id=req.drawing_id,
        detected_count=len(created),
        balloons=created,
    )


@router.post("/", response_model=BalloonResponse)
def create_balloon(payload: BalloonCreate, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == payload.drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    num = payload.balloon_number or _next_number(payload.drawing_id, db)
    b   = Balloon(**payload.model_dump(exclude={"balloon_number"}), balloon_number=num)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.get("/{balloon_id}", response_model=BalloonResponse)
def get_balloon(balloon_id: int, db: Session = Depends(get_db)):
    b = db.query(Balloon).filter(Balloon.id == balloon_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Balloon not found")
    return b


@router.patch("/{balloon_id}", response_model=BalloonResponse)
def update_balloon(balloon_id: int, payload: BalloonUpdate, db: Session = Depends(get_db)):
    b = db.query(Balloon).filter(Balloon.id == balloon_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Balloon not found")
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(b, field, val)
    db.commit()
    db.refresh(b)
    return b


@router.delete("/{balloon_id}")
def delete_balloon(balloon_id: int, db: Session = Depends(get_db)):
    b = db.query(Balloon).filter(Balloon.id == balloon_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Balloon not found")
    db.delete(b)
    db.commit()
    return {"message": "Balloon deleted"}