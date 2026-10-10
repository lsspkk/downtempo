"""Sheet music for the player: PDF pages rendered to PNG with pdfium, cached in `data/cache/pages/`."""

import hashlib
import itertools
import shutil
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps

from downtempo.config import DATA_DIR

CACHE_DIR = DATA_DIR / "cache" / "pages"
WIDTH = 1600  # pixels; sharp at full window width, about 150 kB per page
MARGIN = 40  # pixels of white kept around the cropped music


def page_images(pdf: Path) -> list[str]:
    """Names `<key>/<page>.png` under CACHE_DIR, rendered on first use. Slow: call from a thread."""
    stat = pdf.stat()
    key = hashlib.sha1(
        f"{pdf}:{stat.st_mtime_ns}:{stat.st_size}:{WIDTH}".encode()
    ).hexdigest()[:16]
    folder = CACHE_DIR / key
    if not folder.exists():
        partial = CACHE_DIR / f"{key}.partial"
        shutil.rmtree(partial, ignore_errors=True)
        partial.mkdir(parents=True)
        document = pdfium.PdfDocument(pdf)
        for number, page in enumerate(document, 1):
            image = crop(page.render(scale=WIDTH / page.get_width()).to_pil())
            image.save(partial / f"{number:03}.png", optimize=True)
        document.close()
        partial.rename(folder)
    return [f"{key}/{p.name}" for p in sorted(folder.glob("*.png"))]


def crop(image: Image.Image) -> Image.Image:
    """Cut the empty paper around the music: lead sheets often fill only the top half of the page.

    A small footer (page date) far below the music is cut too; the date is also in the file name.
    """
    ink = ImageOps.invert(image.convert("L")).point(lambda v: 255 if v > 32 else 0)
    box = ink.getbbox()
    if box is None:
        return image
    left, top, right, bottom = box
    rows = [
        y for y in range(top, bottom) if ink.crop((0, y, image.width, y + 1)).getbbox()
    ]
    gaps = [(b - a, a, b) for a, b in itertools.pairwise(rows)]
    if gaps:
        gap, above, below = max(gaps)
        if gap > image.height * 0.2 and bottom - below < image.height * 0.05:
            bottom = above + 1
    return image.crop(
        (
            max(left - MARGIN, 0),
            max(top - MARGIN, 0),
            min(right + MARGIN, image.width),
            min(bottom + MARGIN, image.height),
        )
    )
