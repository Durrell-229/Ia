import os
import json
from django.conf import settings
from PIL import Image
from groq import Groq
from .ocr_service import extract_text_from_images

class AIService:
    def __init__(self):
        self.groq_key = getattr(settings, 'GROQ_API_KEY', '')
        self.provider = getattr(settings, 'AI_PROVIDER', 'groq')
        
        if self.groq_key:
            self.client = Groq(api_key=self.groq_key)

    def correct_student_copy(self, model_answer_path: str, student_pages_paths: list, instructions: str = ""):
        """
        Analyse les copies via OCR, puis corrige avec Groq.
        """
        # 1. OCR sur le corrigé type (si nécessaire, ou passer directement le texte)
        # Ici on suppose que model_answer_path est une image nécessitant un OCR
        model_text = extract_text_from_images([model_answer_path])
        
        # 2. OCR sur la copie de l'élève
        student_text = extract_text_from_images(student_pages_paths)

        # 3. Préparation du prompt pour Groq
        prompt = f"""
        Tu es un correcteur d'examens professionnel.
        CORRIGE TYPE : {model_text}
        COPIE DE L'ÉLÈVE : {student_text}
        INSTRUCTIONS : {instructions}
        
        RETOURNE UN JSON STRICT : 
        {{"note_totale": float, "note_max": 20, "appreciation_globale": "string", "details": [{{"question": "string", "note": float, "commentaire": "string"}}]}}
        """

        # 4. Appel Groq
        if self.provider == 'groq' and self.client:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional exam grader. You must output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )
            return json.loads(chat_completion.choices[0].message.content)
        
        return {"error": "Fournisseur IA non configuré ou indisponible"}
