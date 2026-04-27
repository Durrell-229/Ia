import pytesseract
from PIL import Image
import os

def extract_text_from_images(image_paths: list) -> str:
    """
    Extrait le texte de plusieurs images en utilisant PyTesseract.
    """
    text_content = ""
    for path in image_paths:
        try:
            image = Image.open(path)
            text = pytesseract.image_to_string(image, lang='fra+eng')
            text_content += f"\n--- Page {path} ---\n{text}"
        except Exception as e:
            text_content += f"\n--- Erreur OCR sur {path}: {str(e)} ---\n"
    return text_content
