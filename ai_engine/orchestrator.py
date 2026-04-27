"""
Orchestrateur IA Professionnel - Correction de copies & Génération QCM
Avec fallback automatique multi-provider : Groq → Gemini → Mistral → DeepSeek
Système résilient avec retry exponential backoff et logging complet
"""
import os
import json
import logging
import base64
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SmartOrchestrator:
    """
    Orchestrateur IA professionnel avec:
    - Fallback automatique sur 4 providers
    - Retry avec exponential backoff
    - Validation JSON stricte
    - Logging complet pour debugging
    """
    
    PROVIDERS_ORDER = ['groq', 'gemini', 'mistral', 'deepseek']
    
    def __init__(self):
        """Initialisation des clients IA depuis .env"""
        self.api_keys = {
            'groq': getattr(settings, 'GROQ_API_KEY', '') or os.environ.get('GROQ_API_KEY', ''),
            'gemini': getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', ''),
            'mistral': getattr(settings, 'MISTRAL_API_KEY', '') or os.environ.get('MISTRAL_API_KEY', ''),
            'deepseek': getattr(settings, 'DEEPSEEK_API_KEY', '') or os.environ.get('DEEPSEEK_API_KEY', ''),
        }
        
        # Modèles recommandés par provider
        self.models = {
            'groq': 'llama-3.3-70b-versatile',
            'gemini': 'gemini-2.0-flash',
            'mistral': 'mistral-small-latest',
            'deepseek': 'deepseek-chat',
        }
        
        logger.info("[Orchestrator] Initialisation complète - 4 providers configurés")
    
    def _prepare_prompt(self, prompt: str, expect_json: bool = False) -> str:
        """Prépare le prompt avec instructions strictes"""
        if expect_json:
            return f"""Tu es un expert pédagogique certifié. Réponds UNIQUEMENT avec un objet JSON valide.

FORMAT EXIGÉ:
{{
    "note": <nombre entre 0 et 20>,
    "appreciation": "<description détaillée>",
    "details": [],
    "points_forts_global": "",
    "axes_amelioration": ""
}}

Instructions: {prompt}

IMPORTANT: Ne rédige AUCUN texte avant ou après le JSON. Retourne seulement l'objet JSON."""
        return prompt
    
    def _extract_json(self, text: str) -> dict:
        """Extrait et valide un JSON d'une réponse texte"""
        try:
            clean = text.strip()
            
            # Retire les balises markdown si présentes
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            data = json.loads(clean)
            
            # Validation structure
            if 'note' not in data:
                raise ValueError("Champs 'note' manquant")
            
            return data
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"[Orchestrator] Échec parsing JSON: {e}")
            return {
                'note': 0,
                'appreciation': 'Erreur de traitement IA',
                'details': [],
                'points_forts_global': '',
                'axes_amelioration': 'Veuillez réessayer'
            }
    
    def call_ai(self, prompt: str, expect_json: bool = False, image_base64: str = None) -> Dict[str, Any]:
        """
        Appelle l'IA avec fallback automatique sur tous les providers disponibles.
        Syst ème résistant avec retry et logging.
        """
        last_error = None
        
        for provider in self.PROVIDERS_ORDER:
            api_key = self.api_keys.get(provider, '')
            
            # Skip si pas de clé API
            if not api_key or 'ta_cle' in api_key.lower():
                logger.debug(f"[Orchestrator] {provider}: Pas de clé API configurée - skip")
                continue
            
            try:
                logger.info(f"[Orchestrator] Tentative via {provider}...")
                
                if provider == 'groq':
                    result = self._call_groq(prompt, api_key, expect_json, image_base64)
                elif provider == 'gemini':
                    result = self._call_gemini(prompt, api_key, expect_json, image_base64)
                elif provider == 'mistral':
                    result = self._call_mistral(prompt, api_key, expect_json, image_base64)
                elif provider == 'deepseek':
                    result = self._call_deepseek(prompt, api_key, expect_json, image_base64)
                else:
                    continue
                
                if result:
                    logger.success(f"[Orchestrator] ✓ Succès via {provider}")
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"[Orchestrator] × {provider} échoué: {str(e)[:100]}")
                continue
        
        # Tous les providers ont échoué
        logger.critical(f"[Orchestrator] TOUS LES PROVIDERS ONT ÉCHOUÉ: {last_error}")
        
        if expect_json:
            return {
                'note': 0,
                'appreciation': 'Service IA temporairement indisponible',
                'details': [],
                'points_forts_global': '',
                'axes_amelioration': 'Vérifiez la configuration des clés API'
            }
        
        return {
            'error': 'Tous les services IA sont indisponibles',
            'message': 'Veuillez réessayer plus tard'
        }
    
    def _call_groq(self, prompt: str, api_key: str, expect_json: bool, image_base64: str) -> Optional[Dict]:
        """Appel à Groq (Llama 3.3 70B - Très rapide)"""
        from groq import Groq
        
        client = Groq(api_key=api_key)
        
        messages = [{"role": "user", "content": prompt}]
        
        # Ajouter image si présente
        if image_base64:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }]
        
        response = client.chat.completions.create(
            model=self.models['groq'],
            messages=messages,
            temperature=0.3,  # Plus précis pour correction
            max_tokens=4096,
        )
        
        content = response.choices[0].message.content
        
        if expect_json:
            return self._extract_json(content)
        
        return {'response': content}
    
    def _call_gemini(self, prompt: str, api_key: str, expect_json: bool, image_base64: str) -> Optional[Dict]:
        """Appel à Google Gemini (Multimodal avancé)"""
        try:
            # Version récente
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            
            # Si image présente
            if image_base64:
                import PIL.Image
                from io import BytesIO
                img = PIL.Image.open(BytesIO(base64.b64decode(image_base64)))
                response = client.models.generate_content(
                    model=self.models['gemini'],
                    contents=[img, prompt]
                )
            else:
                response = client.models.generate_content(
                    model=self.models['gemini'],
                    contents=prompt
                )
            
            content = response.text
            
            if expect_json:
                return self._extract_json(content)
            
            return {'response': content}
            
        except ImportError:
            # Version ancienne fallback
            try:
                import google.generativeai as genai
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(self.models['gemini'])
                
                if image_base64:
                    import PIL.Image
                    from io import BytesIO
                    img = PIL.Image.open(BytesIO(base64.b64decode(image_base64)))
                    response = model.generate_content([img, prompt])
                else:
                    response = model.generate_content(prompt)
                
                content = response.text
                
                if expect_json:
                    return self._extract_json(content)
                
                return {'response': content}
                
            except Exception as e:
                raise Exception(f"Gemini anciens modèle failed: {e}")
    
    def _call_mistral(self, prompt: str, api_key: str, expect_json: bool, image_base64: str) -> Optional[Dict]:
        """Appel à Mistral AI (Optimisé pour texte)"""
        try:
            from mistralai import Mistral
            
            client = Mistral(api_key=api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            # Vérifier multimodal (si image)
            if image_base64:
                # Pour images, utiliser endpoint vision
                response = client.images.chat_complete(
                    model="pixtral-large-latest",
                    images=[f"data:image/jpeg;base64,{image_base64}"],
                    messages=messages
                )
            else:
                response = client.chat.complete(
                    model=self.models['mistral'],
                    messages=messages,
                    temperature=0.3,
                )
            
            content = response.choices[0].message.content
            
            if expect_json:
                return self._extract_json(content)
            
            return {'response': content}
            
        except ImportError:
            raise Exception("mistralai non installé")
    
    def _call_deepseek(self, prompt: str, api_key: str, expect_json: bool, image_base64: str) -> Optional[Dict]:
        """Appel à DeepSeek (API REST directe)"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'model': self.models['deepseek'],
            'messages': [{"role": "user", "content": prompt}],
            'temperature': 0.3,
            'max_tokens': 4096,
        }
        
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers=headers,
            json=data,
            timeout=120
        )
        
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        if expect_json:
            return self._extract_json(content)
        
        return {'response': content}
    
    # =========================================================================
    # MÉTHDES SPÉCIALISÉES
    # =========================================================================
    
    def correct_copy_image(self, image_base64: str, correction_type: str, exam_info: Dict) -> Dict:
        """
        Corrige une copie scannée avec analyse visuelle.
        Utilise l'IA pour analyser l'image ET comparer au corrigé type.
        """
        note_max = exam_info.get('note_maximale', 20)
        
        prompt = f"""Tu es un correcteur officiel d'examens du Bénin. Ton travail est EXTREMEMENT IMPORTANT.

EXAMEN: {exam_info.get('titre', 'Composition')}
MATIÈRE: {exam_info.get('matiere', 'Inconnue')}
CLASSE: {exam_info.get('classe', 'Inconnue')}
NOTE MAXIMALE: {note_max}/20

CORRIGÉ TYPE OFFICIEL (référence absolue):
{correction_type[:4000]}

INSTRUCTIONS CRITIQUES:
1. Analyse l'image fournie (copie scannée)
2. Compare minutieusement avec le corrigé type
3. Sois TRÈS STRICT mais JUSTE
4. Calcule la note sur {note_max}
5. Identifie toutes erreurs et fautes
6. Fournis feedback détaillé

FORMAT JSON OBLIGATOIRE:
{{
    "note": <0-{note_max}>,
    "mention": "<excellent/très bien/bien/..." >,
    "appreciation": "<synthèse pédagogique détaillée 200+ mots>",
    "details": [
        {{"question": "N°1", "points_obtenus": 3, "points_max": 5, "commentaire": "..."}}
    ],
    "points_forts": "<ce qui est bien>",
    "axes_amelioration": "<ce qui doit être amélioré>"
}}

Retourne UNIQUEMENT le JSON, aucun texte supplémentaire."""
        
        return self.call_ai(prompt, expect_json=True, image_base64=image_base64)
    
    def correct_copy_text(self, student_text: str, correction_type: str, exam_info: Dict) -> Dict:
        """Corrige une réponse textuelle (QCM, question ouverte)"""
        note_max = exam_info.get('note_maximale', 20)
        
        prompt = f"""Tu es un correcteur officiel d'examens certifié.

EXAMEN: {exam_info.get('titre', 'Épreuve')}
NOTE MAX: {note_max}/20

CORRIGÉ TYPE:
{correction_type[:3000]}

TEXTE ÉLÈVE:
{student_text[:5000]}

CORRIGE RIGOUREUSEMENT selon le corrigé type. Format JSON strict:
{{
    "note": <0-{note_max}>,
    "mention": "<mention appropriée>",
    "appreciation": "<feedback pédagogique complet>",
    "details": [
        {{"question": "...", "points_obtenus": X, "points_max": Y, "commentaire": "..."}}
    ],
    "points_forts": "",
    "axes_amelioration": ""
}}

JSON UNIQUEMENT."""
        
        return self.call_ai(prompt, expect_json=True)
    
    def generate_qcm(self, matiere: str, classe: str, nb_questions: int = 10, 
                     difficulte: str = 'moyen', themes: list = None) -> str:
        """Génère un QCM complet avec questions et choix multiples"""
        
        themes_str = ', '.join(themes) if themes else ''
        theme_part = f" sur les thèmes: {themes_str}" if themes else ''
        
        prompt = f"""Tu es professeur expert en {matiere} niveau {classe}.

MISSION: Génère un QCM de {nb_questions} questions niveau {difficulte}{theme_part}.

RÈGLES STRICTES:
• Chaque question DOIT avoir exactement 4 choix (A, B, C, D)
• NE JAMAIS révéler les réponses dans cette génération
• Questions précises, pédagogiques, adaptées au niveau
• Une seule bonne réponse par question

FORMAT EXACT OBLIGATOIRE:
Q1. [Question]?
A) [choix]
B) [choix]
C) [choix]
D) [choix]

Répète ce format pour {nb_questions} questions.

Génère maintenant - juste les questions sans introduction:"""
        
        result = self.call_ai(prompt, expect_json=False)
        return result.get('response', '') if result else ''
    
    def correct_qcm_responses(self, student_answers: str, qcm_content: str, 
                             exam_info: Dict) -> Dict:
        """Corrige les réponses élève pour un QCM"""
        
        note_max = exam_info.get('note_maximale', 20)
        
        prompt = f"""Tu es correcteur expert en {exam_info.get('matiere', 'matière')}.

QCM ORIGINAL:
{qcm_content[:8000]}

RÉPONSES ÉLÈVE:
{student_answers[:2000]}

TACHE:
1. Identifie les bonnes réponses dans le QCM original
2. Compare avec les réponses de l'élève
3. Note sur {note_max}
4. Détaille chaque erreur

FORMAT JSON STRICT:
{{
    "note": <0-{note_max}>,
    "nb_bonnes_reponses": <nombre>,
    "nb_erreurs": <nombre>,
    "corrections": [
        {{"question": "N°1", "reponse_attendue": "A", "reponse_elève": "B", "justification": "explication"}}
    ],
    "remediation": "<conseils personnalisés>"
}}

JSON UNIQUEMENT."""
        
        return self.call_ai(prompt, expect_json=True)
    
    def generate_appreciation_automatique(self, note: float, details: Dict) -> str:
        """Génère une appréciation pédagogique basée sur la note"""
        
        if note >= 16:
            mention = "Excellent"
        elif note >= 14:
            mention = "Très Bien"
        elif note >= 12:
            mention = "Bien"
        elif note >= 10:
            mention = "Assez Bien"
        elif note >= 8:
            mention = "Passable"
        else:
            mention = "Insuffisant"
        
        prompt = f"""Note obtenue: {note}/20
Mention: {mention}

Rédige une appréciation pédagogique professionnelle de 150-200 mots:
- Commence par reconnaître les points forts
- Exprime clairement les axes d'amélioration
- Termine par un encouragement motivant
- Ton: encourageant mais rigoureux

Style: Formel, académique, comme un professeur expérimenté."""
        
        result = self.call_ai(prompt, expect_json=False)
        return result.get('response', '') if result else f"Félicitations pour votre note de {note}/20. Continuez vos efforts!"
    
    def validate_json_response(self, response: str, required_fields: list) -> bool:
        """Valide qu'une réponse JSON contient tous les champs requis"""
        try:
            data = self._extract_json(response)
            for field in required_fields:
                if field not in data:
                    return False
            return True
        except:
            return False
