import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
from pathlib import Path

RENDER_CACHE = Path("render_cache")
RENDER_CACHE.mkdir(exist_ok=True)


def get_page_count(file_path: str, content_type: str) -> int:
    if content_type == "application/pdf":
        import fitz
        doc   = fitz.open(file_path)
        count = doc.page_count
        doc.close()
        return count
    return 1


def render_page_to_png(file_path: str, page: int = 1, dpi: int = 150) -> str:
    key = hashlib.md5(f"{file_path}:{page}:{dpi}".encode()).hexdigest()
    out = RENDER_CACHE / f"{key}.png"

    if out.exists():
        return str(out)

    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        import fitz
        doc = fitz.open(file_path)
        p   = doc[page - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = p.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out))
        doc.close()
    else:
        from PIL import Image
        img = Image.open(file_path).convert("RGB")
        img.thumbnail((4000, 4000))
        img.save(str(out), "PNG")

    return str(out)