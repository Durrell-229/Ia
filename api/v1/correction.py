from ninja import Router, Schema
from compositions.models import Resultat
import uuid
from typing import List

router = Router()

class ResultatOut(Schema):
    id: uuid.UUID
    eleve_name: str
    exam_titre: str
    note: float
    mention: str

@router.get("/", response=List[ResultatOut])
def list_results(request):
    results = Resultat.objects.select_related('session__eleve', 'session__exam').all()
    return [{
        "id": r.id,
        "eleve_name": r.session.eleve.full_name,
        "exam_titre": r.session.exam.titre,
        "note": float(r.note),
        "mention": r.mention
    } for r in results]
