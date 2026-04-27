import json
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def generate_qcm_from_course(cours_text: str, nb_questions: int, createur_id: str, matiere_id: str = None):
    """Génère des questions QCM à partir d'un cours en utilisant l'IA."""
    from accounts.models import User
    from core.models import Matiere
    from .models import QuestionBank, Choice

    createur = User.objects.get(id=createur_id)
    matiere = Matiere.objects.filter(id=matiere_id).first() if matiere_id else None

    prompt = f"""
Tu es un expert en pédagogie et en création de QCM.

COURS / CONTENU :
---
{cours_text[:30000]}
---

Génère exactement {nb_questions} questions à choix multiples basées STRICTEMENT sur ce cours.

Chaque question doit avoir exactement 4 choix dont 1 seule bonne réponse.

Retourne UNIQUEMENT un JSON valide avec cette structure :
{{
  "questions": [
    {{
      "texte": "Question...",
      "difficulte": "facile|moyen|difficile",
      "explication": "Explication de la réponse...",
      "choix": [
        {{"texte": "Choix A", "est_correct": false}},
        {{"texte": "Choix B", "est_correct": true}},
        {{"texte": "Choix C", "est_correct": false}},
        {{"texte": "Choix D", "est_correct": false}}
      ]
    }}
  ]
}}
"""

    try:
        if settings.AI_PROVIDER == 'gemini' and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            text = response.text
        elif settings.AI_PROVIDER == 'deepseek' and settings.DEEPSEEK_API_KEY:
            import requests
            headers = {'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'}
            data = {'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}], 'response_format': {'type': 'json_object'}}
            resp = requests.post('https://api.deepseek.com/chat/completions', headers=headers, json=data, timeout=120)
            resp.raise_for_status()
            text = resp.json()['choices'][0]['message']['content']
        else:
            logger.error("Aucune clé API IA configurée.")
            return {"status": "error", "error": "Aucune clé API configurée"}

        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]

        data = json.loads(text.strip())
        created = 0

        for q_data in data.get('questions', []):
            question = QuestionBank.objects.create(
                matiere=matiere,
                createur=createur,
                texte=q_data['texte'],
                explication=q_data.get('explication', ''),
                difficulte=q_data.get('difficulte', 'moyen'),
                generee_par_ia=True,
                source_cours=cours_text[:500],
            )
            for idx, c_data in enumerate(q_data.get('choix', [])):
                Choice.objects.create(
                    question=question,
                    texte=c_data['texte'],
                    est_correct=c_data.get('est_correct', False),
                    ordre=idx,
                )
            created += 1

        logger.info(f"{created} questions QCM générées par IA pour le cours.")
        return {"status": "success", "questions_created": created}

    except Exception as e:
        logger.error(f"Erreur génération QCM IA: {e}")
        return {"status": "error", "error": str(e)}
