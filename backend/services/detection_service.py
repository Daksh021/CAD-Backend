import os
import re
import shutil
from collections import defaultdict
from typing import Any

import cv2
import numpy as np
import pytesseract
from PIL import Image

from services.pdf_service import render_page_to_png


# ---------------------------
# TESSERACT SETUP
# ---------------------------

def _configure_tesseract() -> None:
    """
    Try to locate Tesseract on Windows if it is not already on PATH.
    If it is already available, do nothing.
    """
    if shutil.which("tesseract"):
        return

    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\tools\Tesseract-OCR\tesseract.exe",
    ]

    for path in candidates:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"Tesseract found at: {path}")
            return

    raise RuntimeError(
        "Tesseract not found. Install it and add it to PATH, or place it in a common Windows install location."
    )

# ---------------------------
# CONFIG
# ---------------------------

MAX_BALLOONS = 30
MIN_CONFIDENCE = 35

# Keep OCR passes light so auto-detect stays responsive
OCR_CONFIGS = ("--oem 3 --psm 6", "--oem 3 --psm 11")


# ---------------------------
# TEXT HELPERS
# ---------------------------

def clean_text(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    # Allow numbers, letters, degrees (°), +/-, diameters (Ø), and basic punctuation
    text = re.sub(r"[^A-Za-z0-9\s.\-+°Øx()/,_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    alpha = sum(ch.isalpha() for ch in text)
    return alpha / max(len(text), 1)


def is_cad_feature(text: str) -> bool:
    """
    Identify if text is a mechanical drawing feature using strict pattern matching.
    """
    text = clean_text(text).upper()

    if not text:
        return False

    # Standard CAD view/section callouts
    if re.search(r"\b(SECTION|VIEW|DETAIL)\s+[A-Z](-[A-Z])?\b", text):
        return True

    # Remove all spaces and typical OCR artifact characters to analyze the core string
    core = text.replace(" ", "").replace(",", ".")
    # Common OCR mistakes
    core = core.replace("O", "0").replace("I", "1")

    # Pure dimensions: 12.5, R3, M8, 039, 1X45
    if re.fullmatch(r"^[RMSO0]?[0-9]+(\.[0-9]+)?(X[0-9]+)?$", core):
        # Reject isolated single digits (e.g. "1", "2") to avoid grid numbers and OCR noise.
        # Valid single digit dimensions are extremely rare in mechanical drawings without tolerances.
        if re.fullmatch(r"^[0-9]$", core):
            return False
        return True

    # Tolerances: +0.150, -0.000
    if re.fullmatch(r"^[+-][0-9]+(\.[0-9]+)?$", core):
        return True
        
    # Tolerances like H12
    if re.fullmatch(r"^H[0-9]+$", core):
        return True
        
    # Dimensions with tolerance class: 10H12, 39H8
    if re.fullmatch(r"^[0-9]+H[0-9]+$", core):
        return True

    return False


def safe_float(value: Any, default: float = -1.0) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def normalize_label(text: str) -> str:
    return clean_text(text).upper().replace(" ", "")


# ---------------------------
# GEOMETRY HELPERS
# ---------------------------

def merge_bbox(indices, data):
    xs, ys, x2s, y2s = [], [], [], []

    for i in indices:
        x = int(data["left"][i])
        y = int(data["top"][i])
        w = int(data["width"][i])
        h = int(data["height"][i])

        xs.append(x)
        ys.append(y)
        x2s.append(x + w)
        y2s.append(y + h)

    return min(xs), min(ys), max(x2s), max(y2s)


def bbox_iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    a_area = max((ax2 - ax1) * (ay2 - ay1), 1)
    b_area = max((bx2 - bx1) * (by2 - by1), 1)

    return inter_area / float(a_area + b_area - inter_area + 1e-6)


def center_dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def make_detection(cx, cy, text, width, height, conf, bbox, stage="ocr"):
    return {
        "x_pct": round(cx / width, 4),
        "y_pct": round(cy / height, 4),
        "type": "note",
        "text": text,
        "description": f"{stage}: {text}",
        "_cx": cx,
        "_cy": cy,
        "_conf": conf,
        "_bbox": bbox,
    }


def strip_internal(detections: list) -> list:
    return [{k: v for k, v in d.items() if not k.startswith("_")} for d in detections]


def dedupe(detections: list) -> list:
    """
    Collapse duplicate OCR hits from multiple image passes.
    """
    if not detections:
        return []

    detections = sorted(detections, key=lambda d: (-d["_conf"], d["_cy"], d["_cx"]))
    kept = []

    for det in detections:
        det_text = normalize_label(det["text"])
        det_cx, det_cy = det["_cx"], det["_cy"]

        duplicate = False

        for ex in kept:
            ex_text = normalize_label(ex["text"])
            ex_cx, ex_cy = ex["_cx"], ex["_cy"]

            dist = center_dist((det_cx, det_cy), (ex_cx, ex_cy))
            iou = bbox_iou(det["_bbox"], ex["_bbox"])

            same_text = det_text == ex_text
            text_overlap = det_text in ex_text or ex_text in det_text

            if (same_text or text_overlap) and (dist < 25 or iou > 0.25):
                duplicate = True
                break

            if dist < 18 and iou > 0.20:
                duplicate = True
                break

        if not duplicate:
            kept.append(det)

    return kept


# ---------------------------
# PREPROCESSING
# ---------------------------

def sharpen(gray: np.ndarray) -> np.ndarray:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(gray, -1, kernel)


def preprocess_variants(gray: np.ndarray):
    variants = []

    variants.append(("gray", gray, 1.0))

    up2 = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    variants.append(("up2x", up2, 2.0))
    variants.append(("up2x_sharp", sharpen(up2), 2.0))

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    variants.append(("thresh", thresh, 1.0))

    return variants


# ---------------------------
# OCR DETECTION
# ---------------------------

def ocr_cad_features(gray: np.ndarray, width: int, height: int) -> list:
    detections = []

    for variant_name, variant, scale in preprocess_variants(gray):
        for config in OCR_CONFIGS:
            data = pytesseract.image_to_data(
                variant,
                output_type=pytesseract.Output.DICT,
                config=config,
            )

            grouped = defaultdict(list)

            for i in range(len(data["text"])):
                raw = clean_text(data["text"][i])
                if not raw:
                    continue

                conf = safe_float(data["conf"][i], default=-1.0)
                if conf < MIN_CONFIDENCE:
                    continue

                key = (
                    int(data["block_num"][i]),
                    int(data["par_num"][i]),
                    int(data["line_num"][i]),
                )
                grouped[key].append(i)

            for indices in grouped.values():
                indices = sorted(indices, key=lambda idx: int(data["left"][idx]))

                words = [clean_text(data["text"][i]) for i in indices if clean_text(data["text"][i])]
                if not words:
                    continue

                phrase = clean_text(" ".join(words)).upper()
                if not is_cad_feature(phrase):
                    continue

                x1, y1, x2, y2 = merge_bbox(indices, data)

                if scale != 1.0:
                    x1 /= scale
                    y1 /= scale
                    x2 /= scale
                    y2 /= scale

                # Better center: average of word centers
                xs, ys = [], []
                for i in indices:
                    x = int(data["left"][i]) / scale
                    y = int(data["top"][i]) / scale
                    w = int(data["width"][i]) / scale
                    h = int(data["height"][i]) / scale
                    xs.append(x + w / 2)
                    ys.append(y + h / 2)

                if xs and ys:
                    cx = sum(xs) / len(xs)
                    cy = sum(ys) / len(ys)
                else:
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2

                # Determine balloon type based on content
                b_type = "dimension"
                if "SECTION" in phrase or "VIEW" in phrase or "NOTE" in phrase:
                    b_type = "note"
                elif "+" in phrase or "-" in phrase or "MAX" in phrase or "MIN" in phrase:
                    b_type = "tolerance"

                detections.append(
                    make_detection(
                        cx=cx,
                        cy=cy,
                        text=phrase,
                        width=width,
                        height=height,
                        conf=0.9,
                        bbox=(x1, y1, x2, y2),
                        stage="ocr",
                    )
                )

    return detections


# ---------------------------
# CONTOUR FALLBACK
# ---------------------------

def contour_fallback(gray: np.ndarray, width: int, height: int) -> list:
    """
    Conservative fallback when OCR finds too little.
    """
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        11,
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed = cv2.dilate(binary, kernel, iterations=1)

    contours, _ = cv2.findContours(
        morphed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates = []

    # Scale down min_area for CAD dimensions which can be quite small
    min_area = max(40, int(width * height * 0.000005))
    max_area = int(width * height * 0.03)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h

        if area < min_area or area > max_area:
            continue

        if w < 5 or h < 5:
            continue

        aspect = max(w, h) / max(min(w, h), 1)
        if aspect > 15:
            continue

        crop = gray[max(0, y - 2):min(height, y + h + 2), max(0, x - 2):min(width, x + w + 2)]
        if crop.size == 0:
            continue

        crop_up = cv2.resize(crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)

        for config in ("--oem 3 --psm 7", "--oem 3 --psm 8"):
            raw = pytesseract.image_to_string(crop_up, config=config)
            text = clean_text(raw).upper()

            if not is_cad_feature(text):
                continue

            cx = x + w / 2
            cy = y + h / 2

            b_type = "dimension"
            if "+" in text or "-" in text:
                b_type = "tolerance"

            candidates.append(
                make_detection(
                    cx=cx,
                    cy=cy,
                    text=text,
                    width=width,
                    height=height,
                    conf=0.3,
                    bbox=(x, y, x + w, y + h),
                    stage="fallback",
                )
            )
            # Only need to identify it once successfully
            break

    return candidates


# ---------------------------
# MAIN ENTRY
# ---------------------------

def auto_detect_balloons(file_path: str, page_number: int):
    
    _configure_tesseract()
    print("Floor-plan auto detect starting")

    png_path = render_page_to_png(file_path, page_number)
    img = Image.open(png_path).convert("RGB")

    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    height, width = cv_img.shape[:2]
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    print(f"  Image size: {width}x{height}")

    # ---------------------------
    # OCR DETECTION
    # ---------------------------
    detections = ocr_cad_features(gray, width, height)
    print(f"  OCR raw detections: {len(detections)}")

    detections = dedupe(detections)
    print(f"  OCR after dedupe: {len(detections)}")

    # ---------------------------
    # FALLBACK (if OCR weak)
    # ---------------------------
    if len(detections) < 2:
        print("OCR too weak, using fallback")
        fallback = contour_fallback(gray, width, height)
        detections.extend(fallback)
        detections = dedupe(detections)
        print(f"  After fallback + dedupe: {len(detections)}")

    # ---------------------------
    # FINAL COLLAPSE
    # ---------------------------
    final = []

    for det in detections:
        is_duplicate = False

        for ex in final:
            t1 = clean_text(det["text"]).upper().replace(" ", "")
            t2 = clean_text(ex["text"]).upper().replace(" ", "")

            same_text = t1 == t2
            text_overlap = t1 in t2 or t2 in t1

            dist = center_dist((det["_cx"], det["_cy"]), (ex["_cx"], ex["_cy"]))
            iou = bbox_iou(det["_bbox"], ex["_bbox"])

            if (same_text or text_overlap) and (dist < 40 or iou > 0.35):
                is_duplicate = True
                break

            if dist < 20 and iou > 0.20:
                is_duplicate = True
                break

        if not is_duplicate:
            final.append(det)

    print(f"  After final collapse: {len(final)}")

    # ---------------------------
    # ROOM-LEVEL CLUSTERING
    # ---------------------------
    clustered = []

    for det in final:
        keep = True

        for ex in clustered:
            dist = center_dist((det["_cx"], det["_cy"]), (ex["_cx"], ex["_cy"]))

            t1 = normalize_label(det["text"])
            t2 = normalize_label(ex["text"])

            # Only remove if SAME label nearby
            if t1 == t2 and dist < 80:
                keep = False
                break

        if keep:
            clustered.append(det)

    final = clustered
    print(f"  After room clustering: {len(final)}")

    # ---------------------------
    # SORT + LIMIT
    # ---------------------------
    final.sort(key=lambda d: (d["y_pct"], d["x_pct"]))
    final = final[:MAX_BALLOONS]

    # ---------------------------
    # CLEAN OUTPUT
    # ---------------------------
    final = strip_internal(final)

    print(f"Final balloon count: {len(final)}")
    return final