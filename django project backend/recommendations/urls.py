"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 RECOMMENDATION URLS - URL Routing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='recommendations-health'),
    
    # Index movies (admin)
    path('index-movies/', views.index_movies, name='index-movies'),
    
    # Get trending/popular movies
    path('trending/', views.get_trending, name='get-trending'),
    
    # Get personalized recommendations
    path('<str:username>/', views.get_recommendations, name='get-recommendations'),
    
    # Get similar movies
    path('similar/<str:movie_id>/', views.get_similar_movies, name='get-similar-movies'),
    
    # Get personalized sections (NEW - all 10 sections)
    path('sections/<str:username>/', views.get_personalized_sections, name='get-personalized-sections'),
    
    # Regenerate personalized sections (force update)
    path('sections/<str:username>/regenerate/', views.regenerate_personalized_sections, name='regenerate-personalized-sections'),
]
