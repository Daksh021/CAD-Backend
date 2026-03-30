from pydantic import BaseModel


class ExportRequest(BaseModel):
    drawing_id: int
    include_remarks: bool = True