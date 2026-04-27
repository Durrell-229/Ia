from ninja import Router, Schema
from api.services.ai_service import AIService
import uuid

router = Router()

class ChatSchema(Schema):
    message: str

@router.post("/ask")
def ask_tutor(request, data: ChatSchema):
    """
    Endpoint de PRODUCTION pour le Tuteur IA.
    Aucune simulation : utilise l'IA configurée dans le .env
    """
    if not request.user.is_authenticated:
        return {"response": "Veuillez vous connecter pour accéder au tuteur."}, 401
        
    ai_service = AIService()
    
    # Construction du prompt de production
    full_prompt = f"""
    Tu es le Tuteur IA officiel de l'Académie Numérique.
    Utilisateur : {request.user.full_name}
    Rôle : {request.user.get_role_display()}
    
    Mission : Répondre de manière pédagogique, précise et concise. 
    Si la question n'est pas liée à l'éducation, rappelle poliment ta mission.
    
    Question : {data.message}
    """
    
    try:
        # Appel réel
        if ai_service.provider == 'gemini':
            response = ai_service._call_gemini(full_prompt)
        else:
            response = ai_service._call_deepseek(full_prompt)
            
        return {"response": response}
    except Exception as e:
        return {"response": "Erreur de connexion avec l'IA. Vérifiez votre clé API."}, 500
