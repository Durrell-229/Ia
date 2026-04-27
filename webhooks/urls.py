from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.webhook_list_view, name='webhook_list'),
    path('create/', views.webhook_create_api, name='webhook_create'),
    path('deliveries/<str:webhook_id>/', views.webhook_deliveries_view, name='webhook_deliveries'),
    path('test/', views.public_webhook_test, name='webhook_test'),
]
