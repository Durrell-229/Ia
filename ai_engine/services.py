import os
import logging
import json
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Tentative d'import de Groq
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Nouvelle bibliothèque Gemini (google-genai) supportée
try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    try:
        import google.generativeai as old_genai
        HAS_NEW_GENAI = False
    except ImportError:
        HAS_NEW_GENAI = None


def extract_text_from_file(file_path: str) -> str:
    """Extrait le texte d'un fichier (texte brut, PDF, ou image via OCR)."""
    if not os.path.exists(file_path):
        logger.warning(f"Fichier introuvable: {file_path}")
        return ""
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # Fichiers texte
    if ext in ['.txt', '.md', '.csv']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erreur lecture fichier texte {file_path}: {e}")
            return ""
    
    # Fichiers PDF
    if ext == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            logger.warning("PyMuPDF non installé, tentative de lecture brute")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception:
                return ""
        except Exception as e:
            logger.error(f"Erreur lecture PDF {file_path}: {e}")
            return ""
    
    # Fichiers image (OCR)
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
        try:
            from PIL import Image
            import pytesseract
            image = Image.open(file_path)
            return pytesseract.image_to_string(image, lang='fra')
        except ImportError:
            logger.warning("Pillow ou pytesseract non installé pour OCR")
            return "[Image - OCR non disponible]"
        except Exception as e:
            logger.error(f"Erreur OCR {file_path}: {e}")
            return ""
    
    # Autre format : tenter lecture brute
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""


def build_correction_prompt(corrige_type_text: str, copie_text: str, exam_info: dict) -> str:
    return f"""
Tu es un correcteur d'examens professionnel et strict.

INFORMATIONS DE L'EXAMEN :
- Titre : {exam_info.get('titre', '')}
- Note maximale : {exam_info.get('note_maximale', 20)}

CORRIGE TYPE (référence absolue) :
---
{corrige_type_text}
---

COPIE DE L'ELEVE :
---
{copie_text}
---

INSTRUCTIONS CRITIQUES :
1. Corrige EXACTEMENT selon le corrigé type fourni ci-dessus.
2. Attribue une note sur {exam_info.get('note_maximale', 20)}.
3. Fournis une appréciation détaillée.
4. Retourne UNIQUEMENT un objet JSON valide avec cette structure :
{{
  "note": <nombre>,
  "appreciation": "<texte>",
  "details": [
    {{"question": "<texte>", "points": <nombre>, "commentaire": "<texte>"}}
  ],
  "points_forts_global": "<texte>",
  "axes_amelioration": "<texte>"
}}
"""

class AIService:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or getattr(settings, 'AI_PROVIDER', 'gemini')
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        self.groq_key = getattr(settings, 'GROQ_API_KEY', '')

        # Initialisation Gemini si nécessaire
        if self.provider == 'gemini' and self.gemini_key:
            if HAS_NEW_GENAI:
                self.client = genai.Client(api_key=self.gemini_key)
            elif HAS_NEW_GENAI is False:
                old_genai.configure(api_key=self.gemini_key)
        
        # Initialisation Groq si nécessaire
        if self.provider == 'groq' and self.groq_key and HAS_GROQ:
            self.groq_client = Groq(api_key=self.groq_key)

    def correct_copy(self, corrige_type_text: str, copie_text: str, exam_info: dict) -> dict:
        prompt = build_correction_prompt(corrige_type_text, copie_text, exam_info)

        if self.provider == 'gemini' and self.gemini_key:
            return self._call_gemini(prompt)
        elif self.provider == 'deepseek' and self.deepseek_key:
            return self._call_deepseek(prompt)
        elif self.provider == 'groq' and self.groq_key and HAS_GROQ:
            return self._call_groq(prompt)
        else:
            logger.warning(f"Fournisseur IA '{self.provider}' non configuré ou clé manquante.")
            return self._fallback_correction(exam_info)

    def _call_gemini(self, prompt: str) -> dict:
        try:
            if HAS_NEW_GENAI:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                return json.loads(response.text)
            else:
                model = old_genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                text = response.text
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0]
                elif '```' in text:
                    text = text.split('```')[1].split('```')[0]
                return json.loads(text.strip())
        except Exception as e:
            logger.error(f"Erreur Gemini: {e}")
            return self._fallback_correction({})

    def _call_deepseek(self, prompt: str) -> dict:
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {"role": "system", "content": "You are a professional exam grader. You must output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                'response_format': {'type': 'json_object'},
            }
            resp = requests.post('https://api.deepseek.com/chat/completions', headers=headers, json=data, timeout=120)
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"Erreur DeepSeek: {e}")
            return self._fallback_correction({})

    def _call_groq(self, prompt: str) -> dict:
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional exam grader. You must output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )
            content = chat_completion.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Erreur Groq: {e}")
            return self._fallback_correction({})

    def _fallback_correction(self, exam_info: dict) -> dict:
        note_max = exam_info.get('note_maximale', 20)
        return {
            "note": 0,
            "appreciation": "Erreur technique lors de la correction. Veuillez réessayer ou contacter un administrateur.",
            "details": [],
            "points_forts_global": "",
            "axes_amelioration": "",
        }

# Instance globale
ai_service = AIService()
