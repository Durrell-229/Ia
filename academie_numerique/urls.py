from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from core.views import home_view, admin_dashboard_view

from core.api_urls import api as core_api
from api.v1.router import api as v1_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('showcase/', include('video_showcase.urls')),
    path('app/', home_view, name='home'),
    path('api/v1/', v1_api.urls),
    path('api/core/', core_api.urls),
    path('accounts/', include('accounts.urls')),
    path('exams/', include('exams.urls')),
    path('compositions/', include('compositions.urls')),
    path('notifications/', include('notifications.urls')),
    path('correction/', include('correction.urls')),
    path('bulletins/', include('bulletins.urls')),
    path('certificates/', include('certifications.urls')),
    path('qcm/', include('qcm.urls')),
    path('plagiat/', include('plagiat.urls')),
    path('gamification/', include('gamification.urls')),
    path('audit/', include('audittrail.urls')),
    path('webhooks/', include('webhooks.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('videoconf/', include('videoconf.urls')),
    path('forums/', include('social.urls')),
    path('calendar/', include('calendar_app.urls')),
    path('documents/', include('documents.urls')),
    path('analytics/', include('analytics.urls')),
]

# Redirect root to showcase
from django.views.generic import RedirectView
urlpatterns.insert(0, path('', RedirectView.as_view(url='/showcase/', permanent=False)))

# Servir les fichiers médias et statiques en développement (RIGOUREUX)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += staticfiles_urlpatterns()
