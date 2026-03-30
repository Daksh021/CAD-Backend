from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from models import BalloonType


class BalloonBase(BaseModel):
    drawing_id: int
    balloon_number: int
    page_number: int = 1
    x_pct: float
    y_pct: float
    balloon_type: BalloonType = BalloonType.NOTE
    extracted_text: Optional[str] = None
    description: Optional[str] = None
    remarks: Optional[str] = None
    is_auto: int = 1


class BalloonCreate(BalloonBase):
    pass


class BalloonResponse(BalloonBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

class BalloonUpdate(BaseModel):
    balloon_number: Optional[int] = None
    x_pct: Optional[float] = None
    y_pct: Optional[float] = None
    description: Optional[str] = None
    remarks: Optional[str] = None