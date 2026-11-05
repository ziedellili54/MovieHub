"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 RECOMMENDATION API VIEWS - REST Endpoints
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    REST API endpoints for the AI recommendation system
    Connects the recommendation engine to the frontend

ENDPOINTS:
    1. POST /api/recommendations/index-movies/ - Index all movies (admin)
    2. GET /api/recommendations/{username}/ - Get personalized recommendations
    3. GET /api/recommendations/similar/{movie_id}/ - Get similar movies
    4. POST /api/recommendations/refresh-user/{username}/ - Refresh user profile

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .recommendation_engine import RecommendationEngine
from datetime import datetime
from movies.models import Movie, TVShow
from accounts.analytics_models import UserPreferences
import os


# Initialize recommendation engine (singleton pattern)
recommendation_engine = None


def get_engine():
    """Get or create recommendation engine instance"""
    global recommendation_engine
    if recommendation_engine is None:
        recommendation_engine = RecommendationEngine()
    return recommendation_engine


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 1: Index Movies (Admin Only - Run Periodically)
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
def index_movies(request):
    """
    Index all movies in vector database for recommendations
    
    POST /api/recommendations/index-movies/
    
    Body: None (indexes all movies from MongoDB)
    
    Response:
        {
            "success": true,
            "stats": {
                "movies_indexed": 150,
                "tvshows_indexed": 50,
                "failed": 2,
                "total": 202
            },
            "message": "Successfully indexed 200 items"
        }
    
    Note: This should be run:
        - After initial setup
        - When new movies are added
        - Periodically (weekly) to keep index fresh
    
    Warning: Can take several minutes for large catalogs!
    """
    try:
        engine = get_engine()
        
        # Index all movies
        stats = engine.index_all_movies()
        
        success_count = stats['movies_indexed'] + stats['tvshows_indexed']
        
        return Response({
            'success': True,
            'stats': stats,
            'message': f"Successfully indexed {success_count} items"
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 2: Get Personalized Recommendations
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request, username):
    """
    Get personalized recommendations for a user
    
    GET /api/recommendations/{username}/?count=10&genre=Action&type=Movie
    
    Query Parameters:
        - count (int): Number of recommendations (default: 10)
        - genre (str): Filter by genre (optional)
        - type (str): Filter by type - "Movie" or "TV Show" (optional)
    
    Response:
        {
            "success": true,
            "username": "john",
            "count": 10,
            "recommendations": [
                {
                    "movie_id": "507f1f77bcf86cd799439011",
                    "title": "Interstellar",
                    "type": "Movie",
                    "genres": "Sci-Fi, Drama",
                    "description": "...",
                    "poster": "https://...",
                    "release_year": 2014,
                    "rating": "PG-13",
                    "director": "Christopher Nolan",
                    "cast": "Matthew McConaughey, Anne Hathaway",
                    "similarity_score": 0.92,
                    "reason": "Based on your love for Sci-Fi movies"
                },
                ...
            ]
        }
    
    Frontend Usage:
        // In Angular service
        getRecommendations(username: string, count: number = 10) {
            return this.http.get(`/api/recommendations/${username}/?count=${count}`);
        }
    """
    try:
        engine = get_engine()
        
        # Get query parameters
        count = int(request.GET.get('count', 10))
        genre = request.GET.get('genre', None)
        movie_type = request.GET.get('type', None)
        
        # Build filters
        filters = {}
        if genre:
            filters['genre'] = genre
        if movie_type:
            filters['type'] = movie_type
        
        # Get recommendations
        recommendations = engine.get_recommendations(
            username=username,
            n_recommendations=count,
            filters=filters if filters else None
        )
        
        return Response({
            'success': True,
            'username': username,
            'count': len(recommendations),
            'filters': filters if filters else {},
            'recommendations': recommendations
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'recommendations': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 3: Get Similar Movies
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([AllowAny])
def get_similar_movies(request, movie_id):
    """
    Get movies similar to a specific movie
    
    GET /api/recommendations/similar/{movie_id}/?count=5
    
    Query Parameters:
        - count (int): Number of similar movies (default: 5)
    
    Response:
        {
            "success": true,
            "movie_id": "507f1f77bcf86cd799439011",
            "count": 5,
            "similar_movies": [
                {
                    "movie_id": "507f191e810c19729de860ea",
                    "title": "Inception",
                    "type": "Movie",
                    "genres": "Action, Sci-Fi, Thriller",
                    "poster": "https://...",
                    "similarity_score": 0.88
                },
                ...
            ]
        }
    
    Use Case:
        Display "If you liked this, you'll love these" section
        on movie detail page
    
    Frontend Usage:
        // On movie detail page
        getSimilarMovies(movieId: string) {
            return this.http.get(`/api/recommendations/similar/${movieId}/`);
        }
    """
    try:
        engine = get_engine()
        
        # Get query parameters
        count = int(request.GET.get('count', 5))
        
        # Get similar movies
        similar_movies = engine.get_similar_movies(
            movie_id=movie_id,
            n_results=count
        )
        
        return Response({
            'success': True,
            'movie_id': movie_id,
            'count': len(similar_movies),
            'similar_movies': similar_movies
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'similar_movies': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 4: Get Trending/Popular Movies
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([AllowAny])
def get_trending(request):
    """
    Get trending/popular movies - CURRENT TRENDING (2020+)
    
    Strategy: Show 2020+ content sorted by rating + popularity
    """
    try:
        # Get query parameters
        count = int(request.GET.get('count', 20))
        movie_type = request.GET.get('type', None)
        username = request.GET.get('username', None)
        
        # Get CURRENT trending content (2020+)
        all_content = []
        
        if not movie_type or movie_type == 'Movie':
            # Get 2020+ movies WITH good ratings
            recent_rated = list(Movie.objects(release_year__gte=2020, imdb_rating__gte=6.5).order_by('-imdb_rating', '-imdb_votes'))
            all_content.extend(recent_rated)
            
        if not movie_type or movie_type == 'TV Show':
            # Get 2020+ series WITH good ratings
            recent_rated = list(TVShow.objects(release_year__gte=2020, imdb_rating__gte=7.0).order_by('-imdb_rating', '-imdb_votes'))
            all_content.extend(recent_rated)
        
        # Filter out disliked movies
        if username:
            try:
                from accounts.analytics_models import MovieDislike
                dislikes = MovieDislike.objects(username=username)
                disliked_ids = set([str(dislike.movie_id) for dislike in dislikes])
                
                if disliked_ids:
                    all_content = [m for m in all_content if str(m.id) not in disliked_ids]
            except:
                pass
        
        # Sort by IMDB rating (highest first)
        all_content.sort(key=lambda x: getattr(x, 'imdb_rating', 0), reverse=True)
        
        # Format response
        trending = []
        for item in all_content[:count]:
            trending.append({
                'id': str(item.id),
                'movie_id': str(item.id),
                'title': item.title,
                'type': getattr(item, 'type', 'Movie'),
                'genres': getattr(item, 'listed_in', ''),
                'listed_in': getattr(item, 'listed_in', ''),
                'primary_category': getattr(item, 'primary_category', ''),
                'description': getattr(item, 'description', ''),
                'poster': getattr(item, 'poster', None),
                'release_year': getattr(item, 'release_year', 0),
                'rating': getattr(item, 'rating', ''),
                'director': getattr(item, 'director', ''),
                'cast': getattr(item, 'cast', ''),
                'imdb_rating': getattr(item, 'imdb_rating', 0.0),
                'imdb_votes': getattr(item, 'imdb_votes', 0),
                'similarity_score': 0.0,
                'reason': '🔥 Trending Now'
            })
        
        return Response({
            'success': True,
            'count': len(trending),
            'trending': trending
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'trending': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 5: Health Check
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Check if recommendation system is properly configured
    
    GET /api/recommendations/health/
    
    Response:
        {
            "success": true,
            "status": "healthy",
            "model": "sentence-transformers (local)",
            "indexed_movies_count": 200
        }
    """
    try:
        # Check Vector DB
        ready = False
        indexed_count = 0
        
        try:
            engine = get_engine()
            indexed_count = engine.movies_collection.count()
            ready = True
        except:
            pass
        
        is_healthy = ready and indexed_count > 0
        
        return Response({
            'success': True,
            'status': 'healthy' if is_healthy else 'not_indexed',
            'model': 'tensorflow-hub-use-v4 (512-dim, free)',
            'indexed_movies_count': indexed_count,
            'message': 'Recommendation system is ready!' if is_healthy else 'Please index movies first'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 API ENDPOINTS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENDPOINT                                     METHOD  PURPOSE
────────────────────────────────────────────────────────────────────────────
/api/recommendations/health/                 GET     Check system status
/api/recommendations/index-movies/           POST    Index all movies (admin)
/api/recommendations/{username}/             GET     Get personalized recommendations
/api/recommendations/similar/{movie_id}/     GET     Get similar movies

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""



# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 5: Get Personalized Sections for User Dashboard
# ═══════════════════════════════════════════════════════════════════════════

def reorder_genres_for_user(listed_in, preferred_genres):
    """Re-order genre string so user's top preferred genres appear FIRST as card badge pills"""
    if not listed_in or not preferred_genres:
        return listed_in or ''
    genres = [g.strip() for g in listed_in.split(',') if g.strip()]
    pref_lower = [p.lower() for p in preferred_genres]
    
    def sort_key(g):
        g_lower = g.lower()
        for rank, p in enumerate(pref_lower):
            if p == g_lower or p in g_lower or g_lower in p:
                return rank
        return 99
    
    sorted_g = sorted(genres, key=sort_key)
    return ', '.join(sorted_g)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_personalized_sections(request, username):
    """
    Get all personalized dashboard sections for a user
    
    GET /api/recommendations/sections/{username}/
    
    Returns 10 sections:
    1. AI Recommendations (20 movies)
    2. Top Watched Movies
    3. Top Watched Series
    4. Top Searched Movies
    5. Top Searched Series
    6. Top 10 Movies
    7. Top 10 Series
    8. Top 20 Favorites
    9. Newly Added Movies
    10. Newly Added Series
    
    Each section contains movie IDs sorted by user's genre preferences
    
    Response:
        {
            "success": true,
            "username": "john",
            "last_updated": "2026-08-05T10:00:00",
            "sections": {
                "ai_recommendations": {
                    "movies": [{movie details...}],
                    "metadata": {...}
                },
                "top_watched_movies": {
                    "movies": [{movie details...}],
                    "scores": {...}
                },
                ...
            }
        }
    """
    try:
        from recommendations.personalized_sections_engine import PersonalizedSectionsEngine
        from bson import ObjectId
        
        # Generate/get sections
        engine = PersonalizedSectionsEngine()
        sections_data = engine.generate_sections_for_user(username)
        
        if not sections_data:
            return Response({
                'success': False,
                'error': 'Could not generate sections'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Fetch full movie details for each section
        result = {
            'success': True,
            'username': username,
            'last_updated': datetime.utcnow().isoformat(),
            'sections': {}
        }
        
        # Helper to fetch movies by IDs
        user_prefs_obj = UserPreferences.objects(username=username).first()
        user_fav_genres = user_prefs_obj.favorite_genres if user_prefs_obj else []

        def fetch_movies(movie_ids):
            """Optimized batch fetch"""
            if not movie_ids:
                return []
            
            print(f"[DEBUG] fetch_movies called with {len(movie_ids)} IDs")
            print(f"[DEBUG] First 3 IDs: {movie_ids[:3]}")
            
            movies = []
            try:
                from bson import ObjectId as BsonObjectId
                
                # Convert all IDs at once
                obj_ids = [BsonObjectId(mid) for mid in movie_ids]
                print(f"[DEBUG] Converted to {len(obj_ids)} ObjectIds")
                
                # Batch fetch movies
                fetched_movies = {str(m.id): m for m in Movie.objects(id__in=obj_ids)}
                fetched_series = {str(s.id): s for s in TVShow.objects(id__in=obj_ids)}
                
                print(f"[DEBUG] Fetched {len(fetched_movies)} movies, {len(fetched_series)} series")
                
                # Preserve order from movie_ids
                for mid in movie_ids:
                    item = fetched_movies.get(mid) or fetched_series.get(mid)
                    if not item:
                        continue
                    
                    is_series = mid in fetched_series
                    movies.append({
                        'id': str(item.id),
                        'movie_id': str(item.id),
                        'title': item.title,
                        'type': 'TV Show' if is_series else 'Movie',
                        'genres': reorder_genres_for_user(getattr(item, 'listed_in', ''), user_fav_genres) if not is_series else getattr(item, 'listed_in', ''),
                        'listed_in': reorder_genres_for_user(getattr(item, 'listed_in', ''), user_fav_genres) if not is_series else getattr(item, 'listed_in', ''),
                        'primary_category': getattr(item, 'primary_category', ''),
                        'description': getattr(item, 'description', ''),
                        'poster': getattr(item, 'poster', None),
                        'release_year': getattr(item, 'release_year', 0),
                        'rating': getattr(item, 'rating', ''),
                        'director': getattr(item, 'director', ''),
                        'cast': getattr(item, 'cast', ''),
                        'imdb_rating': getattr(item, 'imdb_rating', 0.0),
                        'imdb_votes': getattr(item, 'imdb_votes', 0)
                    })
                
                print(f"[DEBUG] Returning {len(movies)} movies")
            except Exception as e:
                print(f"[ERROR] fetch_movies failed: {e}")
                import traceback
                traceback.print_exc()
            
            return movies
        
        # Build response for each section
        for section_name, section_data in sections_data.items():
            if 'ids' in section_data:
                result['sections'][section_name] = {
                    'movies': fetch_movies(section_data['ids']),
                    'metadata': section_data.get('metadata', {}),
                    'scores': section_data.get('scores', {}),
                    'dates': section_data.get('dates', {})
                }
        
        return Response(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 6: Force Regenerate Personalized Sections
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
def regenerate_personalized_sections(request, username):
    """
    Force regenerate personalized sections for a user
    Use when user changes preferences or after significant activity
    
    POST /api/recommendations/sections/{username}/regenerate/
    
    Response:
        {
            "success": true,
            "message": "Sections regenerated successfully"
        }
    """
    try:
        from recommendations.personalized_sections_engine import PersonalizedSectionsEngine
        
        engine = PersonalizedSectionsEngine()
        sections_data = engine.generate_sections_for_user(username, force_regenerate=True)
        
        if sections_data:
            return Response({
                'success': True,
                'message': 'Sections regenerated successfully'
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to regenerate sections'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
