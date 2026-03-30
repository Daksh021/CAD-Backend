from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DrawingBase(BaseModel):
    filename: str
    original_name: str
    file_path: str
    page_count: int = 1
    width_px: Optional[float] = None
    height_px: Optional[float] = None


class DrawingCreate(DrawingBase):
    pass


class DrawingResponse(DrawingBase):
    id: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrawingDetail(DrawingResponse):
    pass