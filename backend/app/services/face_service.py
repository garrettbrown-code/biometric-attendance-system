from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageOps


def _fr():
    """
    Lazy import wrapper for face_recognition.
    Tests can patch this to avoid importing the real dependency.
    """
    import face_recognition

    return face_recognition


@dataclass(frozen=True)
class FaceMatchResult:
    status: str  # "success" | "error"
    error: str | None = None


import base64

def _decode_base64_to_bytes(photo_b64: str) -> bytes:
    # Strip data URI prefix if present: "data:image/jpeg;base64,...."
    if photo_b64.startswith("data:"):
        photo_b64 = photo_b64.split(",", 1)[1]

    # Make decoding tolerant to missing '=' padding (common on clients)
    photo_b64 = photo_b64.strip()
    missing = (-len(photo_b64)) % 4
    if missing:
        photo_b64 += "=" * missing

    try:
        # validate=False allows standard base64 variants safely for our use case
        return base64.b64decode(photo_b64, validate=False)
    except Exception as e:
        raise ValueError("photo must be valid base64") from e


def _load_image_from_bytes(image_bytes: bytes, fr):
    """
    Loads an image from bytes and returns a numpy array suitable for face_recognition.
    Normalizes EXIF orientation before conversion.
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # Best-effort EXIF normalization:
    # - Real PIL Images support EXIF methods.
    # - Tests may patch Image.open to return a lightweight fake that does not.
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    img = img.convert("RGB")

    jpeg_bytes = _pil_to_jpeg_bytes(img)
    return fr.load_image_file(io.BytesIO(jpeg_bytes))


def _pil_to_jpeg_bytes(img: Image.Image) -> bytes:
    """
    Converts a PIL image to JPEG bytes. Helps normalize formats (png, etc.) to a standard.
    """
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def save_reference_image(*, photo_b64: str, dest_path: Path) -> None:
    """
    Persist the student's reference image to disk.
    Normalize orientation so face_recognition can detect faces reliably.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Strip data-uri prefix if present (defensive)
    if photo_b64.startswith("data:"):
        photo_b64 = photo_b64.split(",", 1)[1]

    raw = _decode_base64_to_bytes(photo_b64)

    # Normalize with Pillow to avoid sideways reference images (common on mobile captures)
    try:
        img = Image.open(BytesIO(raw))
        img = ImageOps.exif_transpose(img)  # applies EXIF orientation if present
        img = img.convert("RGB")
        img.save(dest_path, format="JPEG", quality=95)
    except Exception:
        # If Pillow fails, fall back to raw bytes (better than failing enrollment)
        dest_path.write_bytes(raw)


def _get_first_encoding(image_arr, fr):
    """
    Returns the first face encoding or None.
    """
    encodings = fr.face_encodings(image_arr)
    if not encodings:
        return None
    return encodings[0]


def verify_face_match(
    *,
    submitted_photo_b64: str,
    reference_image_path: Path,
    tolerance: float = 0.6,
) -> FaceMatchResult:
    # IMPORTANT: check this first so tests don't import face_recognition
    if not reference_image_path.exists():
        return FaceMatchResult(status="error", error="Reference image not found")

    if submitted_photo_b64.startswith("data:"):
        submitted_photo_b64 = submitted_photo_b64.split(",", 1)[1]

    try:
        submitted_bytes = _decode_base64_to_bytes(submitted_photo_b64)
    except ValueError as e:
        return FaceMatchResult(status="error", error=str(e))

    fr = _fr()  # lazy import here (after early exits)

    try:
        reference_arr = fr.load_image_file(str(reference_image_path))
    except Exception:
        return FaceMatchResult(status="error", error="Unable to load reference image")

    try:
        submitted_arr = _load_image_from_bytes(submitted_bytes, fr)
    except Exception:
        return FaceMatchResult(status="error", error="Unable to load submitted image")

    ref_encoding = _get_first_encoding(reference_arr, fr)
    if ref_encoding is None:
        return FaceMatchResult(status="error", error="No face detected in reference image")

    sub_encoding = _get_first_encoding(submitted_arr, fr)
    if sub_encoding is None:
        return FaceMatchResult(status="error", error="No face detected in submitted image")

    matches = fr.compare_faces([ref_encoding], sub_encoding, tolerance=tolerance)
    is_match = bool(matches and matches[0])

    if is_match:
        return FaceMatchResult(status="success")
    return FaceMatchResult(status="error", error="Face does not match reference")
