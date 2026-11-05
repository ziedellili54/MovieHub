"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👎 MOVIE DISLIKE API - Hidden Dislike System with AI Impact
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Allow users to dislike movies, hide them, and penalize AI

KEY FEATURES:
    1. Hidden from user (unlike favorites which are visible)
    2. Removes movie from ALL sections (recommendations, trending, packs)
    3. Penalizes AI if it recommended the disliked movie
    4. Learns genre patterns to avoid similar content
    5. Tracks dislike reasons for analytics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .analytics_models import MovieDislike, RecommendationFeedback, UserPreferences
from movies.models import Movie, TVShow
from datetime import datetime
from bson import ObjectId


class DislikeMovieView(APIView):
    """
    Dislike a movie (hidden, affects AI)
    
    POST /api/dislikes/
    
    Body:
    {
        "username": "john",
        "movie_id": "abc123",
        "dislike_reason": "not_interested",  // optional
        "was_ai_recommendation": false,      // optional
        "recommendation_position": null      // optional (if AI recommended)
    }
    
    Response:
    {
        "success": true,
        "message": "Movie disliked and hidden",
        "ai_penalty": -15,  // If AI recommended
        "genre_penalties": {"Horror": -10, "Thriller": -5}
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            username = data.get('username')
            movie_id_str = data.get('movie_id')
            
            if not username or not movie_id_str:
                return Response({
                    'success': False,
                    'error': 'username and movie_id required'
                }, status=400)
            
            # Get movie details
            movie = None
            try:
                # Try to convert to ObjectId if it's a valid ID
                try:
                    obj_id = ObjectId(movie_id_str)
                except:
                    obj_id = movie_id_str
                
                movie = Movie.objects.get(id=obj_id)
            except:
                try:
                    # Try again with string directly
                    movie = Movie.objects.get(id=movie_id_str)
                except:
                    try:
                        # Try as TVShow
                        try:
                            obj_id = ObjectId(movie_id_str)
                        except:
                            obj_id = movie_id_str
                        movie = TVShow.objects.get(id=obj_id)
                    except:
                        try:
                            movie = TVShow.objects.get(id=movie_id_str)
                        except:
                            return Response({
                                'success': False,
                                'error': f'Movie not found with ID: {movie_id_str}'
                            }, status=404)
            
            # Check if already disliked
            existing = MovieDislike.objects(username=username, movie_id=movie_id_str).first()
            if existing:
                return Response({
                    'success': True,
                    'message': 'Already disliked',
                    'disliked_at': existing.disliked_at.isoformat()
                })
            
            # Extract genres for penalty calculation
            genres = []
            if hasattr(movie, 'listed_in') and movie.listed_in:
                genres = [g.strip() for g in movie.listed_in.split(',')]
            
            # Calculate genre penalties
            genre_penalty_weights = {}
            for i, genre in enumerate(genres[:3]):  # Top 3 genres
                if i == 0:
                    genre_penalty_weights[genre] = -10  # Primary genre: -10
                elif i == 1:
                    genre_penalty_weights[genre] = -5   # Secondary: -5
                else:
                    genre_penalty_weights[genre] = -3   # Tertiary: -3
            
            # Calculate AI penalty if it was a recommendation
            was_ai_rec = data.get('was_ai_recommendation', False)
            rec_position = data.get('recommendation_position')
            ai_penalty = 0
            
            if was_ai_rec and rec_position:
                # AI penalty: worse if it was recommended early (should be good)
                if rec_position <= 10:
                    ai_penalty = -20  # Top 10 should be good, big penalty
                elif rec_position <= 30:
                    ai_penalty = -10  # Top 30, medium penalty
                else:
                    ai_penalty = -5   # Lower ranks, small penalty
                
                # Create negative feedback for AI
                feedback = RecommendationFeedback(
                    username=username,
                    recommendation_batch_id=f"dislike_{datetime.utcnow().strftime('%Y%m%d')}_{username}",
                    recommended_movie_id=movie_id_str,
                    recommended_movie_title=movie.title,
                    recommendation_position=rec_position,
                    similarity_score=0,  # Unknown
                    recommended_genres=genres,
                    feedback_score=ai_penalty,
                    feedback_category="disliked",
                    user_favorite_genres_at_time=[],
                    total_recommendations_in_batch=100,
                    skipped_count=0,
                    recommended_at=datetime.utcnow(),
                    clicked_at=datetime.utcnow()
                )
                feedback.save()
            
            # Create dislike record
            dislike = MovieDislike(
                username=username,
                movie_id=movie_id_str,
                movie_title=movie.title,
                movie_type=getattr(movie, 'type', 'Movie'),
                genres=genres,
                director=getattr(movie, 'director', ''),
                cast=getattr(movie, 'cast', ''),
                dislike_reason=data.get('dislike_reason', 'not_interested'),
                was_ai_recommendation=was_ai_rec,
                recommendation_position=rec_position,
                ai_penalty_applied=was_ai_rec,
                ai_penalty_score=ai_penalty,
                hide_from_recommendations=True,
                hide_from_trending=True,
                hide_from_search=False,
                genre_penalty_weights=genre_penalty_weights,
                disliked_at=datetime.utcnow()
            )
            dislike.save()
            
            # Update user preferences to reduce these genres
            try:
                prefs = UserPreferences.objects.get(username=username)
                if not prefs.recommendation_score:
                    prefs.recommendation_score = {}
                
                # Reduce genre scores
                for genre, penalty in genre_penalty_weights.items():
                    current = prefs.recommendation_score.get(genre, 50)
                    prefs.recommendation_score[genre] = max(0, current + penalty)
                
                prefs.save()
            except:
                pass
            
            return Response({
                'success': True,
                'message': 'Movie disliked and will be hidden',
                'movie_title': movie.title,
                'ai_penalty': ai_penalty if was_ai_rec else None,
                'genre_penalties': genre_penalty_weights,
                'hidden_from': ['recommendations', 'trending', 'packs']
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class GetDislikesView(APIView):
    """
    Get all disliked movies for a user (for admin/debugging only)
    NOT shown in regular UI
    
    GET /api/dislikes/{username}/
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            dislikes = MovieDislike.objects(username=username).order_by('-disliked_at')
            
            result = []
            for dislike in dislikes:
                result.append({
                    'movie_id': dislike.movie_id,
                    'movie_title': dislike.movie_title,
                    'genres': dislike.genres,
                    'dislike_reason': dislike.dislike_reason,
                    'was_ai_recommendation': dislike.was_ai_recommendation,
                    'ai_penalty_score': dislike.ai_penalty_score,
                    'disliked_at': dislike.disliked_at.isoformat() if dislike.disliked_at else None
                })
            
            return Response({
                'success': True,
                'username': username,
                'total_dislikes': len(result),
                'dislikes': result
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class RemoveDislikeView(APIView):
    """
    Remove a dislike (allow movie to appear again)
    
    DELETE /api/dislikes/
    
    Body:
    {
        "username": "john",
        "movie_id": "abc123"
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def delete(self, request):
        try:
            data = request.data
            username = data.get('username')
            movie_id = data.get('movie_id')
            
            dislike = MovieDislike.objects(username=username, movie_id=movie_id).first()
            if not dislike:
                return Response({
                    'success': False,
                    'error': 'Dislike not found'
                }, status=404)
            
            movie_title = dislike.movie_title
            dislike.delete()
            
            return Response({
                'success': True,
                'message': f'{movie_title} removed from dislikes'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 API ENDPOINTS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENDPOINT                              METHOD  PURPOSE
────────────────────────────────────────────────────────────────────────────────
/api/dislikes/                        POST    Dislike a movie (hides it, penalizes AI)
/api/dislikes/{username}/             GET     Get all dislikes (admin/debug)
/api/dislikes/                        DELETE  Remove dislike (allow movie again)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
