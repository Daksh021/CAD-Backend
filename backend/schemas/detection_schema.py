from typing import List
from pydantic import BaseModel
from schemas.balloon_schema import BalloonResponse

class AutoDetectRequest(BaseModel):
    drawing_id: int
    page_number: int = 1

class AutoDetectResponse(BaseModel):
    drawing_id: int
    detected_count: int
    balloons: List[BalloonResponse]