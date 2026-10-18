import logging
from typing import Optional
from PIL import Image, ImageOps, ImageFilter
import pytesseract

logger = logging.getLogger("ocr_service")


def preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert("L")
    image = ImageOps.autocontrast(image)

    if image.width < 1500:
        image = image.resize((image.width * 2, image.height * 2))

    image = image.filter(ImageFilter.SHARPEN)

    threshold = 180
    image = image.point(lambda p: 255 if p > threshold else 0)

    return image


def extract_text_from_pil_image(image: Image.Image, psm: int = 6) -> str:
    try:
        processed = preprocess_image(image)
        text = pytesseract.image_to_string(
            processed,
            config=f"--oem 3 --psm {psm}"
        )
        return (text or "").strip()
    except Exception as e:
        logger.warning(f"OCR failed for PIL image: {e}")
        return ""


def extract_text_from_image(file_path: str, psm: int = 6) -> str:
    try:
        image = Image.open(file_path)
        return extract_text_from_pil_image(image, psm=psm)
    except Exception as e:
        logger.warning(f"OCR failed for image {file_path}: {e}")
        return ""


def extract_sparse_text_from_pil_image(image: Image.Image) -> str:
    return extract_text_from_pil_image(image, psm=11)