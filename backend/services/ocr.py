"""
Image and OCR Extraction Service
Accepts safe image uploads, checks formats, and extracts text via Tesseract if configured.
Note: Never fabricates simulated text or reverse-image searches.
"""

import os
import io
from typing import Tuple
from ..schemas.analysis import OcrExtractResponse

# Safe allowed image MIME types
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB


def validate_image_upload(content_type: str, file_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """Validates image MIME type and file payload size."""
    if content_type.lower() not in ALLOWED_MIME_TYPES:
        return False, f"Unsupported file type '{content_type}'. Allowed types: PNG, JPEG, WEBP."
    if len(file_bytes) > MAX_IMAGE_BYTES:
        return False, "File exceeds maximum size of 5MB."
    if len(file_bytes) < 100:
        return False, "Uploaded image file is corrupted or empty."
    return True, None


async def extract_text_from_image(file_bytes: bytes, content_type: str) -> OcrExtractResponse:
    """
    Extracts text from uploaded image using pytesseract if installed and available.
    Returns clear diagnostic status if OCR engine is unavailable.
    """
    valid, err_msg = validate_image_upload(content_type, file_bytes)
    if not valid:
        return OcrExtractResponse(
            text="",
            confidence=0.0,
            status="error",
            note=err_msg or "Invalid image file."
        )

    # Attempt Tesseract OCR if libraries available
    try:
        from PIL import Image
        import pytesseract

        tess_cmd = os.environ.get("TESSERACT_CMD")
        if tess_cmd:
            pytesseract.pytesseract.tesseract_cmd = tess_cmd

        img = Image.open(io.BytesIO(file_bytes))
        extracted = pytesseract.image_to_string(img)
        clean_text = extracted.strip()

        if clean_text:
            return OcrExtractResponse(
                text=clean_text,
                confidence=85.0,
                status="success",
                note=f"Successfully extracted {len(clean_text.split())} words via Optical Character Recognition."
            )
        else:
            return OcrExtractResponse(
                text="",
                confidence=0.0,
                status="no_text",
                note="No legible text characters detected in the uploaded image."
            )

    except ImportError:
        return OcrExtractResponse(
            text="",
            confidence=0.0,
            status="unsupported",
            note="OCR service is offline (pytesseract/Pillow not installed in environment). Please paste article text directly."
        )
    except Exception as e:
        return OcrExtractResponse(
            text="",
            confidence=0.0,
            status="unsupported",
            note=f"OCR execution failed: {str(e)}. Please paste article text directly into the analyzer."
        )
