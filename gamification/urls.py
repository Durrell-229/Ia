from django.urls import path
from . import views

urlpatterns = [
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('api/leaderboard/', views.leaderboard_api, name='leaderboard_api'),
    path('my-badges/', views.my_badges_view, name='my_badges'),
    path('my-progress/', views.my_progress_view, name='my_progress'),
]
