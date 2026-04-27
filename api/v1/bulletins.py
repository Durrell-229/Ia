from ninja import Router, Schema
from bulletins.models import Bulletin
import uuid
from typing import List

router = Router()

@router.get("/{eleve_id}")
def list_eleve_bulletins(request, eleve_id: uuid.UUID):
    return Bulletin.objects.filter(eleve_id=eleve_id)

@router.post("/generate/{eleve_id}")
def generate_bulletin(request, eleve_id: uuid.UUID, periode: str):
    # Logique d'agrégation et appel au PDFService
    pass
