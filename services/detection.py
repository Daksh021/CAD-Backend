import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
    # Windows — set tesseract path
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from services.pdf_service import render_page_to_png

_DIMENSION_RE = re.compile(r"\d+(\.\d+)?\s*(mm|in|\"|\u00b0|deg|±|\+|-)", re.IGNORECASE)
_TOLERANCE_RE = re.compile(r"[±]\s*\d|ISO\s*\d+|ASME|tol", re.IGNORECASE)
_GDT_RE       = re.compile(r"flatness|perpendicularity|runout|cylindricity", re.IGNORECASE)
_SURFACE_RE   = re.compile(r"Ra\s*\d|Rz\s*\d|N\d{1,2}", re.IGNORECASE)
_NOTE_RE      = re.compile(r"(NOTE|SEE|REF|SPEC|ALL|TYP|MATERIAL|FINISH)", re.IGNORECASE)


def _classify(text: str) -> str:
    if _DIMENSION_RE.search(text): return "dimension"
    if _TOLERANCE_RE.search(text): return "tolerance"
    if _GDT_RE.search(text):       return "gdt"
    if _SURFACE_RE.search(text):   return "surface_finish"
    if _NOTE_RE.search(text):      return "note"
    return "note"


def auto_detect_balloons(file_path: str, page: int = 1) -> list[dict]:
    png_path = render_page_to_png(file_path, page, dpi=200)
    img      = Image.open(png_path).convert("RGB")
    cv_img   = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    h, w     = cv_img.shape[:2]

    if not OCR_AVAILABLE:
        return _fallback_grid(w, h)

    grey   = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    blur   = cv2.GaussianBlur(grey, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    tsv = pytesseract.image_to_data(
        thresh,
        config="--psm 11 --oem 3",
        output_type=pytesseract.Output.DICT,
    )

    detections = []
    seen       = set()

    for i in range(len(tsv["text"])):
        text = tsv["text"][i].strip()
        conf = int(tsv["conf"][i])
        if conf < 40 or len(text) < 2 or text in seen:
            continue
        seen.add(text)

        cx = tsv["left"][i] + tsv["width"][i]  / 2
        cy = tsv["top"][i]  + tsv["height"][i] / 2

        detections.append({
            "x_pct":       round(cx / w * 100, 2),
            "y_pct":       round(cy / h * 100, 2),
            "type":        _classify(text),
            "text":        text,
            "description": text,
        })

    detections.sort(key=lambda d: (round(d["y_pct"] / 5), d["x_pct"]))
    return detections[:50]


def _fallback_grid(w: int, h: int, n: int = 6) -> list[dict]:
    cols, result = 3, []
    rows = (n + cols - 1) // cols
    for r in range(rows):
        for c in range(cols):
            if len(result) >= n:
                break
            result.append({
                "x_pct":       round((c + 1) / (cols + 1) * 100, 2),
                "y_pct":       round((r + 1) / (rows + 1) * 100, 2),
                "type":        "note",
                "text":        f"Item {len(result) + 1}",
                "description": f"Auto-detected item {len(result) + 1}",
            })
    return result