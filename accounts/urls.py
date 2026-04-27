from django.urls import path
from . import views, views_supervision

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('supervision/', views_supervision.supervision_view, name='supervision'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]
