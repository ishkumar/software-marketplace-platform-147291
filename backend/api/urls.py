from django.urls import path
from .views import health
from .auth_views import (
    register, login_view, logout_view, profile,
    google_login, github_login,
)

urlpatterns = [
    path('health/', health, name='Health'),
    path('auth/register/', register, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/profile/', profile, name='profile'),
    path('auth/google/', google_login, name='google-login'),
    path('auth/github/', github_login, name='github-login'),
]
