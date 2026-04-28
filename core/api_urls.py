from ninja import NinjaAPI
from django.http import JsonResponse

from accounts.api import router as accounts_router
from exams.api import router as exams_router
from compositions.api import router as compositions_router
from core.public_api import router as public_router
from videoconf.api import router as videoconf_router

api = NinjaAPI(
    title="Académie Numérique API",
    version="2.0.0",
    description="API mondiale pour la composition et l'évaluation en ligne. Intègre certification, QCM, plagiat, gamification, webhooks et plus.",
    docs_url="/docs/",
)

api.add_router("/auth", accounts_router, tags=["Authentication"])
api.add_router("/exams", exams_router, tags=["Exams"])
api.add_router("/compositions", compositions_router, tags=["Compositions"])
api.add_router("/public", public_router, tags=["API Publique"])
api.add_router("/videoconf", videoconf_router, tags=["Video Conference"])


@api.exception_handler(Exception)
def global_exception_handler(request, exc):
    return JsonResponse({"error": str(exc)}, status=500)
