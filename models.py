"""
models.py — SQLAlchemy ORM models
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class BalloonType(str, enum.Enum):
    DIMENSION = "dimension"
    TOLERANCE = "tolerance"
    NOTE = "note"
    SPECIFICATION = "specification"
    SURFACE_FINISH = "surface_finish"
    GDT = "gdt"


class Drawing(Base):
    """
    Represents an uploaded 2D engineering drawing (PDF or image).
    """
    __tablename__ = "drawings"

    id            = Column(Integer, primary_key=True, index=True)
    filename      = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_path     = Column(String, nullable=False)
    page_count    = Column(Integer, default=1)
    width_px      = Column(Float, nullable=True)   # rendered width in px
    height_px     = Column(Float, nullable=True)   # rendered height in px
    uploaded_at   = Column(DateTime, default=datetime.utcnow)

    balloons = relationship("Balloon", back_populates="drawing", cascade="all, delete-orphan")


class Balloon(Base):
    """
    A single balloon annotation placed on a drawing.
    x, y are expressed as percentage of drawing width/height (0–100)
    so they remain valid across zoom levels.
    """
    __tablename__ = "balloons"

    id             = Column(Integer, primary_key=True, index=True)
    drawing_id     = Column(Integer, ForeignKey("drawings.id"), nullable=False)
    balloon_number = Column(Integer, nullable=False)
    page_number    = Column(Integer, default=1)

    # Position — stored as % of image dimension
    x_pct          = Column(Float, nullable=False)
    y_pct          = Column(Float, nullable=False)

    balloon_type   = Column(Enum(BalloonType), default=BalloonType.NOTE)
    extracted_text = Column(String, nullable=True)   # OCR / detected text
    description    = Column(String, nullable=True)   # user-edited description
    remarks        = Column(String, nullable=True)

    is_auto        = Column(Integer, default=1)       # 1 = auto-generated, 0 = manual
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    drawing = relationship("Drawing", back_populates="balloons")