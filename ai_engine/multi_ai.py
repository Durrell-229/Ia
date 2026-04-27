"""
Service IA multi-provider avec fallback automatique.
Ordre de tentative : Groq → Gemini → Mistral → DeepSeek
"""
import os
import json
import logging
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class MultiAIService:
    """
    Service IA avec fallback automatique sur 4 fournisseurs.
    Ordre : Groq → Gemini → Mistral → DeepSeek
    """

    def __init__(self):
        self.groq_key = getattr(settings, 'GROQ_API_KEY', '') or os.environ.get('GROQ_API_KEY', '')
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        self.mistral_key = getattr(settings, 'MISTRAL_API_KEY', '') or os.environ.get('MISTRAL_API_KEY', '')
        self.deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '') or os.environ.get('DEEPSEEK_API_KEY', '')

    def generate(self, prompt: str, expect_json: bool = False) -> str:
        """
        Envoie un prompt à l'IA disponible.
        Tente chaque fournisseur dans l'ordre jusqu'à succès.
        """
        providers = [
            ('Groq', self._call_groq),
            ('Gemini', self._call_gemini),
            ('Mistral', self._call_mistral),
            ('DeepSeek', self._call_deepseek),
        ]

        for name, fn in providers:
            try:
                result = fn(prompt)
                if result:
                    logger.info(f"[MultiAI] Succès via {name}")
                    return result
            except Exception as e:
                logger.warning(f"[MultiAI] Échec {name}: {e}")
                continue

        logger.error("[MultiAI] Tous les fournisseurs IA ont échoué.")
        if expect_json:
            return '{"note": 0, "appreciation": "IA indisponible.", "details": [], "points_forts_global": "", "axes_amelioration": "Vérifiez les clés API."}'
        return "L'IA est temporairement indisponible. Vérifiez les clés API dans le fichier .env."

    def _call_groq(self, prompt: str) -> Optional[str]:
        if not self.groq_key or 'ta_cle' in self.groq_key:
            return None
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=4096,
            )
            return resp.choices[0].message.content
        except ImportError:
            logger.debug("groq non installé")
            return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        if not self.gemini_key or 'ta_cle' in self.gemini_key:
            return None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return resp.text
        except Exception:
            pass
        try:
            import google.generativeai as old_genai
            old_genai.configure(api_key=self.gemini_key)
            model = old_genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        except Exception:
            return None

    def _call_mistral(self, prompt: str) -> Optional[str]:
        if not self.mistral_key or 'ta_cle' in self.mistral_key:
            return None
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            resp = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
        except ImportError:
            logger.debug("mistralai non installé")
            return None

    def _call_deepseek(self, prompt: str) -> Optional[str]:
        if not self.deepseek_key or 'ta_cle' in self.deepseek_key:
            return None
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': 'deepseek-chat',
                'messages': [{"role": "user", "content": prompt}],
            }
            resp = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers=headers, json=data, timeout=60
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except Exception:
            return None

    def correct_copy(self, corrige_type_text: str, copie_text: str, exam_info: dict) -> dict:
        """Corrige une copie d'élève par rapport à un corrigé type."""
        note_max = exam_info.get('note_maximale', 20)
        prompt = f"""Tu es un correcteur d'examens professionnel et strict pour les grandes écoles du Bénin.

INFORMATIONS DE L'EXAMEN :
- Titre : {exam_info.get('titre', 'Épreuve')}
- Note maximale : {note_max}

CORRIGÉ TYPE (référence absolue) :
---
{corrige_type_text[:3000]}
---

COPIE DE L'ÉLÈVE :
---
{copie_text[:3000]}
---

INSTRUCTIONS CRITIQUES :
1. Corrige EXACTEMENT selon le corrigé type fourni.
2. Attribue une note sur {note_max}.
3. Retourne UNIQUEMENT un objet JSON valide sans texte autour :
{{
  "note": <nombre entre 0 et {note_max}>,
  "appreciation": "<appréciation globale détaillée>",
  "details": [
    {{"question": "<partie>", "points": <nombre>, "commentaire": "<explication>"}}
  ],
  "points_forts_global": "<points forts>",
  "axes_amelioration": "<axes d'amélioration>"
}}"""

        raw = self.generate(prompt, expect_json=True)
        try:
            clean = raw.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0]
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0]
            return json.loads(clean.strip())
        except Exception:
            return {
                "note": 0,
                "appreciation": f"Erreur de parsing IA. Réponse brute: {raw[:500]}",
                "details": [],
                "points_forts_global": "",
                "axes_amelioration": "Vérifiez les clés API."
            }

    def generate_qcm(self, matiere: str, classe: str, nb_questions: int = 10,
                     difficulte: str = 'moyen', theme: str = '') -> str:
        """Génère un QCM complet."""
        theme_str = f" sur le thème spécifique : {theme}" if theme else ""
        prompt = f"""Tu es un professeur expert en {matiere} pour la classe {classe}{theme_str}.

Génère un QCM de {nb_questions} questions de niveau {difficulte}.

RÈGLES STRICTES :
- Chaque question a exactement 4 choix : A, B, C, D
- NE révèle PAS les bonnes réponses dans cette section
- Numérote chaque question : Q1, Q2, Q3...
- Questions précises, pédagogiques et adaptées au niveau {classe}

FORMAT EXACT :
Q1. [Question] ?
A) [Choix A]
B) [Choix B]
C) [Choix C]
D) [Choix D]

Génère les {nb_questions} questions maintenant. Ne fournis que les questions, aucune introduction :"""
        return self.generate(prompt)

    def correct_qcm(self, reponses: str, qcm_original: str, ctx: dict) -> dict:
        """Corrige les réponses à un QCM et retourne un JSON structuré."""
        prompt = f"""Tu es un correcteur expert en {ctx.get('matiere', 'matière')}.

QCM original généré :
---
{qcm_original}
---

Réponses de l'élève :
---
{reponses}
---

Corrige ces réponses. Retourne UNIQUEMENT un JSON valide sans texte autour :
{{
  "note": <nombre entre 0 et 20>,
  "corrections": "<détail par question : bonne réponse et explication>",
  "remediation": "<conseils personnalisés pour progresser>"
}}"""

        raw = self.generate(prompt, expect_json=True)
        try:
            clean = raw.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0]
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0]
            return json.loads(clean.strip())
        except Exception:
            return {"note": 10, "corrections": raw[:1000], "remediation": "Continuez à pratiquer !"}


# Instance globale réutilisable
multi_ai = MultiAIService()
