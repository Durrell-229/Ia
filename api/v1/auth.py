from ninja import Router, Schema
from django.contrib.auth import authenticate, login
from accounts.models import User
from django.conf import settings
from typing import Optional
import uuid

router = Router()

class RegisterSchema(Schema):
    email: str
    password: str
    first_name: str
    last_name: str
    role: str
    role_password: Optional[str] = None
    phone: str = ""
    country: str = "France"
    niveau: str = "secondaire"

class LoginSchema(Schema):
    email: str
    password: str

@router.post("/register")
def register(request, data: RegisterSchema):
    # Vérification du mot de passe de rôle
    if data.role == User.Role.ADMIN:
        if data.role_password != settings.ROLE_PASSWORD_ADMIN:
            return {"error": "Mot de passe Admin invalide"}, 403
    elif data.role == User.Role.CONSEILLER:
        if data.role_password != settings.ROLE_PASSWORD_CP:
            return {"error": "Mot de passe Conseiller invalide"}, 403
    elif data.role == User.Role.PROFESSEUR:
        if data.role_password != settings.ROLE_PASSWORD_PROF:
            return {"error": "Mot de passe Professeur invalide"}, 403
            
    if User.objects.filter(email=data.email).exists():
        return {"error": "Cet email est déjà utilisé"}, 400
        
    user = User.objects.create_user(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        phone=data.phone,
        country=data.country,
        niveau=data.niveau
    )
    return {"message": "Compte créé avec succès", "user_id": str(user.id)}

@router.post("/login")
def login_user(request, data: LoginSchema):
    user = authenticate(email=data.email, password=data.password)
    if user:
        login(request, user)
        return {
            "message": "Connexion réussie",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    return {"error": "Identifiants invalides"}, 401
