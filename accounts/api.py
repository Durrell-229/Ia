from typing import Optional
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.db import IntegrityError

from .models import User, Profile

router = Router()


class RegisterSchema(Schema):
    email: str
    password: str
    first_name: str
    last_name: str
    role: str = 'eleve'
    role_password: Optional[str] = None
    phone: Optional[str] = None
    country: str = 'France'
    niveau: Optional[str] = None
    classe: Optional[str] = None


class LoginSchema(Schema):
    email: str
    password: str


class UserOut(Schema):
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    matricule: Optional[str]
    country: str
    niveau: Optional[str]
    classe: Optional[str]
    avatar: Optional[str]
    dark_mode: bool
    preferred_language: str


class MessageOut(Schema):
    message: str
    success: bool = True


class ErrorOut(Schema):
    error: str
    success: bool = False


def check_role_password(role: str, role_password: Optional[str]) -> bool:
    if role == 'admin':
        return role_password == settings.ROLE_PASSWORD_ADMIN
    elif role == 'conseiller':
        return role_password == settings.ROLE_PASSWORD_CP
    elif role == 'professeur':
        return role_password == settings.ROLE_PASSWORD_PROF
    elif role == 'eleve':
        return True
    return False


@router.post("/register", response={200: MessageOut, 400: ErrorOut})
def register(request: HttpRequest, payload: RegisterSchema):
    if User.objects.filter(email=payload.email).exists():
        return 400, {"error": "Cet email est déjà utilisé.", "success": False}

    if not check_role_password(payload.role, payload.role_password):
        return 400, {"error": "Mot de passe de rôle invalide.", "success": False}

    try:
        user = User.objects.create_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=payload.role,
            phone=payload.phone or '',
            country=payload.country,
            niveau=payload.niveau or '',
            classe=payload.classe or '',
        )
        Profile.objects.create(user=user)
        return 200, {"message": "Inscription réussie !", "success": True}
    except IntegrityError as e:
        return 400, {"error": f"Erreur lors de l'inscription: {str(e)}", "success": False}


@router.post("/login", response={200: MessageOut, 401: ErrorOut})
def login_view(request: HttpRequest, payload: LoginSchema):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is not None:
        login(request, user)
        return 200, {"message": "Connexion réussie.", "success": True}
    return 401, {"error": "Email ou mot de passe incorrect.", "success": False}


@router.post("/logout", response={200: MessageOut})
def logout_view(request: HttpRequest):
    logout(request)
    return 200, {"message": "Déconnexion réussie.", "success": True}


@router.get("/me", response={200: UserOut, 401: ErrorOut})
def me(request: HttpRequest):
    if not request.user.is_authenticated:
        return 401, {"error": "Non authentifié.", "success": False}
    user = request.user
    return 200, {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "role": user.role,
        "matricule": user.matricule,
        "country": user.country,
        "niveau": user.niveau,
        "classe": user.classe,
        "avatar": request.build_absolute_uri(user.avatar.url) if user.avatar else None,
        "dark_mode": user.dark_mode,
        "preferred_language": user.preferred_language,
    }


@router.get("/csrf")
def get_csrf(request: HttpRequest):
    return {"csrfToken": get_token(request)}
