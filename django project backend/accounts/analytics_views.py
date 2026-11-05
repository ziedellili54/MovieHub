"""
Analytics API Views for tracking user behavior
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .analytics_models import UserActivity, UserPreferences, UserSession
from datetime import datetime, timedelta
import uuid


class TrackActivityView(APIView):
    """Track any user activity"""
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            
            # Create activity record
            activity = UserActivity(
                username=data.get('username'),
                session_id=data.get('session_id'),
                activity_type=data.get('activity_type'),
                movie_id=data.get('movie_id'),
                movie_title=data.get('movie_title'),
                movie_type=data.get('movie_type'),
                search_query=data.get('search_query'),
                search_results_count=data.get('search_results_count'),
                watch_duration_seconds=data.get('watch_duration_seconds'),
                watch_percentage=data.get('watch_percentage'),
                total_duration_seconds=data.get('total_duration_seconds'),
                category=data.get('category'),
                genres=data.get('genres', []),
                device_type=data.get('device_type'),
                browser=data.get('browser'),
                os=data.get('os'),
                country=data.get('country'),
                ip_address=data.get('ip_address'),
                time_spent_seconds=data.get('time_spent_seconds'),
                metadata=data.get('metadata', {})
            )
            activity.save()
            
            # Update user preferences asynchronously
            self.update_user_preferences(data.get('username'), data)
            
            # ✅ NEW: Update MovieWatchHistory with current watch percentage
            if data.get('activity_type') == 'movie_watch' and data.get('movie_id'):
                self.update_watch_progress(data)
            
            return Response({
                "success": True,
                "message": "Activity tracked successfully"
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=400)
    
    def update_watch_progress(self, data):
        """
        Update watch progress in MovieWatchHistory
        This tracks where the user stopped watching (for Continue Watching)
        """
        try:
            from pymongo import MongoClient
            from bson.objectid import ObjectId
            import os
            from datetime import datetime
            
            # Connect to MongoDB
            mongo_uri = os.getenv("MONGO_URI")
            client = MongoClient(mongo_uri)
            db = client['MovieApp']
            
            username = data.get('username')
            movie_id = data.get('movie_id')
            watch_percentage = data.get('watch_percentage', 0)
            
            # Find existing watch history record
            existing = db['movie_watch_history'].find_one({
                'username': username,
                'movie_id': movie_id
            })
            
            if existing:
                # Update existing record
                db['movie_watch_history'].update_one(
                    {'_id': existing['_id']},
                    {
                        '$set': {
                            'watch_percentage': watch_percentage,  # Current position (ONLY percentage field)
                            'last_watched': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'completed': watch_percentage >= 90  # Mark as completed if 90%+
                        },
                        '$inc': {
                            'watch_count': 1,  # Increment watch count
                            'total_watch_time_seconds': data.get('watch_duration_seconds', 0),
                            'total_watch_time_minutes': data.get('watch_duration_seconds', 0) // 60
                        }
                    }
                )
            else:
                # Create new watch history record
                genres_list = data.get('genres', [])
                if isinstance(genres_list, str):
                    genres_list = [g.strip() for g in genres_list.split(',')]
                
                watch_time_seconds = data.get('watch_duration_seconds', 0)
                watch_time_minutes = watch_time_seconds // 60
                
                new_record = {
                    'username': username,
                    'movie_id': movie_id,
                    'movie_title': data.get('movie_title', 'Unknown'),
                    'movie_type': data.get('movie_type', 'Movie'),
                    'genres': genres_list,
                    'watch_count': 1,
                    'watch_percentage': watch_percentage,  # Current position (ONLY percentage field)
                    'total_watch_time_seconds': watch_time_seconds,
                    'total_watch_time_minutes': watch_time_minutes,
                    'total_watch_time_hours': round(watch_time_minutes / 60, 2),
                    'completed': watch_percentage >= 90,
                    'first_watched': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'last_watched': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                db['movie_watch_history'].insert_one(new_record)
                
        except Exception as e:
            print(f"Error updating watch progress: {e}")
    
    def update_user_preferences(self, username, data):
        """Update aggregated user preferences"""
        if not username:
            return
        
        try:
            # Get or create preferences
            prefs = UserPreferences.objects(username=username).first()
            if not prefs:
                prefs = UserPreferences(username=username)
            
            activity_type = data.get('activity_type')
            
            # Update based on activity type
            if activity_type == 'movie_watch':
                prefs.total_movies_watched = (prefs.total_movies_watched or 0) + 1
            elif activity_type == 'like':
                prefs.total_movies_liked = (prefs.total_movies_liked or 0) + 1
            elif activity_type == 'dislike':
                prefs.total_movies_disliked = (prefs.total_movies_disliked or 0) + 1
            elif activity_type == 'search':
                prefs.total_searches = (prefs.total_searches or 0) + 1
            elif activity_type == 'purchase':
                prefs.total_purchases = (prefs.total_purchases or 0) + 1
                prefs.last_purchase_date = datetime.utcnow()
            
            # Update genres if provided
            if data.get('genres'):
                current_genres = prefs.favorite_genres or []
                for genre in data.get('genres', []):
                    if genre not in current_genres:
                        current_genres.append(genre)
                prefs.favorite_genres = current_genres[:20]  # Keep top 20
            
            # Update device
            if data.get('device_type'):
                prefs.primary_device = data.get('device_type')
                devices = prefs.devices_used or []
                if data.get('device_type') not in devices:
                    devices.append(data.get('device_type'))
                prefs.devices_used = devices
            
            # Update country
            if data.get('country'):
                prefs.country = data.get('country')
            
            prefs.last_activity = datetime.utcnow()
            prefs.updated_at = datetime.utcnow()
            prefs.save()
        except Exception as e:
            print(f"Error updating preferences: {e}")


class StartSessionView(APIView):
    """Start a new user session"""
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            session_id = str(uuid.uuid4())
            
            session = UserSession(
                username=data.get('username'),
                session_id=session_id,
                device_type=data.get('device_type'),
                browser=data.get('browser'),
                os=data.get('os'),
                country=data.get('country'),
                ip_address=data.get('ip_address')
            )
            session.save()
            
            # Track app_open activity
            UserActivity(
                username=data.get('username'),
                session_id=session_id,
                activity_type='app_open',
                device_type=data.get('device_type'),
                browser=data.get('browser'),
                os=data.get('os'),
                country=data.get('country'),
                ip_address=data.get('ip_address')
            ).save()
            
            return Response({
                "success": True,
                "session_id": session_id
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=400)


class EndSessionView(APIView):
    """End a user session"""
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            
            session = UserSession.objects(session_id=session_id).first()
            if session:
                session.session_end = datetime.utcnow()
                session.duration_seconds = int((session.session_end - session.session_start).total_seconds())
                session.is_active = 'ended'
                session.save()
            
            return Response({"success": True})
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=400)


class GetUserAnalyticsView(APIView):
    """Get analytics for a specific user"""
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            # Get user preferences
            prefs = UserPreferences.objects(username=username).first()
            
            # Get recent activities (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_activities = UserActivity.objects(
                username=username,
                timestamp__gte=thirty_days_ago
            ).order_by('-timestamp')[:100]
            
            # Get session data
            recent_sessions = UserSession.objects(
                username=username
            ).order_by('-session_start')[:10]
            
            # Calculate metrics
            total_watch_time = sum([
                a.watch_duration_seconds or 0 
                for a in UserActivity.objects(username=username, activity_type='movie_watch')
            ])
            
            total_sessions = UserSession.objects(username=username).count()
            avg_session_duration = 0
            if total_sessions > 0:
                total_session_time = sum([
                    s.duration_seconds or 0 
                    for s in UserSession.objects(username=username, duration_seconds__ne=None)
                ])
                if total_session_time > 0:
                    avg_session_duration = total_session_time // total_sessions
            
            return Response({
                "username": username,
                "preferences": {
                    "favorite_genres": prefs.favorite_genres if prefs else [],
                    "total_movies_watched": prefs.total_movies_watched if prefs else 0,
                    "total_movies_liked": prefs.total_movies_liked if prefs else 0,
                    "total_searches": prefs.total_searches if prefs else 0,
                    "primary_device": prefs.primary_device if prefs else "unknown",
                    "country": prefs.country if prefs else "unknown",
                    "last_activity": prefs.last_activity if prefs else None
                },
                "metrics": {
                    "total_watch_time_minutes": total_watch_time // 60,
                    "total_sessions": total_sessions,
                    "average_session_duration_minutes": avg_session_duration // 60
                },
                "recent_activities": [
                    {
                        "type": a.activity_type,
                        "movie_title": a.movie_title,
                        "timestamp": a.timestamp,
                        "device": a.device_type
                    } for a in recent_activities
                ]
            })
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=400)


class GetAllUsersAnalyticsView(APIView):
    """Get analytics for all users (Admin only)"""
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get all users with preferences
            all_prefs = UserPreferences.objects.all()
            
            users_data = []
            for prefs in all_prefs:
                # Get recent activity
                last_activity = UserActivity.objects(
                    username=prefs.username
                ).order_by('-timestamp').first()
                
                users_data.append({
                    "username": prefs.username,
                    "total_movies_watched": prefs.total_movies_watched or 0,
                    "total_searches": prefs.total_searches or 0,
                    "favorite_genres": prefs.favorite_genres or [],
                    "primary_device": prefs.primary_device or "unknown",
                    "country": prefs.country or "unknown",
                    "last_activity": last_activity.timestamp if last_activity else None
                })
            
            return Response({
                "total_users": len(users_data),
                "users": users_data
            })
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=400)



class GetUserMovieWatchPercentagesView(APIView):
    """
    Get watch percentage for EACH MOVIE a user has watched
    Shows per-movie statistics including watch count, time spent, and completion percentage
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            from .analytics_models import MovieWatchHistory
            
            # Get all movies this user has watched
            user_movies = MovieWatchHistory.objects(
                username=username
            ).order_by('-total_watch_time_minutes')
            
            if not user_movies:
                return Response({
                    "username": username,
                    "total_movies": 0,
                    "message": "No watch history found",
                    "movies": []
                })
            
            # Build response with per-movie data
            movies_data = []
            total_watch_time = 0
            completed_count = 0
            
            for movie_watch in user_movies:
                total_watch_time += movie_watch.total_watch_time_minutes or 0
                if movie_watch.completed:  # ✅ FIXED: Boolean check instead of string
                    completed_count += 1
                
                movies_data.append({
                    "movie_id": movie_watch.movie_id,
                    "movie_title": movie_watch.movie_title,
                    "movie_type": movie_watch.movie_type,
                    "watch_count": movie_watch.watch_count,
                    "total_watch_time_minutes": movie_watch.total_watch_time_minutes,
                    "total_watch_time_hours": round(movie_watch.total_watch_time_minutes / 60, 1),
                    "watch_percentage": round(movie_watch.watch_percentage, 1),  # Auto-calculated
                    "watching_percentage": movie_watch.watching_percentage if hasattr(movie_watch, 'watching_percentage') else 0,  # User-editable
                    "completed": movie_watch.completed,
                    "genres": movie_watch.genres,
                    "first_watched": movie_watch.first_watched,
                    "last_watched": movie_watch.last_watched
                })
            
            # Calculate statistics
            avg_percentage = sum([m['watch_percentage'] for m in movies_data]) / len(movies_data) if movies_data else 0
            
            return Response({
                "username": username,
                "total_movies": len(movies_data),
                "statistics": {
                    "total_watch_time_minutes": total_watch_time,
                    "total_watch_time_hours": round(total_watch_time / 60, 1),
                    "movies_completed": completed_count,
                    "completion_rate": round((completed_count / len(movies_data)) * 100, 1) if movies_data else 0,
                    "average_watch_percentage": round(avg_percentage, 1)
                },
                "movies": movies_data
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e)
            }, status=400)


class GetMovieWatchDetailsView(APIView):
    """
    Get detailed watch sessions for a specific movie watched by a user
    Shows every time the user watched this movie
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username, movie_id):
        try:
            from .analytics_models import MovieWatchHistory
            
            # Get aggregated watch history
            watch_history = MovieWatchHistory.objects(
                username=username,
                movie_id=movie_id
            ).first()
            
            if not watch_history:
                return Response({
                    "error": "No watch history found for this movie"
                }, status=404)
            
            # Get all individual watch sessions from UserActivity
            watch_sessions = UserActivity.objects(
                username=username,
                movie_id=movie_id,
                activity_type='movie_watch'
            ).order_by('-timestamp')
            
            sessions_data = []
            for session in watch_sessions:
                sessions_data.append({
                    "timestamp": session.timestamp,
                    "watch_percentage": round(session.watch_percentage, 1) if session.watch_percentage else 0,
                    "watch_duration_minutes": round(session.watch_duration_seconds / 60, 1) if session.watch_duration_seconds else 0,
                    "device_type": session.device_type,
                    "ip_address": session.ip_address
                })
            
            return Response({
                "username": username,
                "movie_id": movie_id,
                "movie_title": watch_history.movie_title,
                "summary": {
                    "total_watch_count": watch_history.watch_count,
                    "total_watch_time_minutes": watch_history.total_watch_time_minutes,
                    "total_watch_time_hours": round(watch_history.total_watch_time_minutes / 60, 1),
                    "watch_percentage": round(watch_history.watch_percentage, 1),  # ✅ FIXED: Single percentage field
                    "completed": watch_history.completed  # ✅ FIXED: Already boolean
                },
                "watch_sessions": sessions_data
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e)
            }, status=400)


class GetContinueWatchingView(APIView):
    """
    Get Continue Watching list for a user (movies/shows with progress < 90%)
    Used by frontend dashboard to show "Continue Watching" section
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            from .analytics_models import MovieWatchHistory
            from movies.models import Movie
            from bson import ObjectId
            
            # Get movies with watching_percentage > 0 (only user-set progress)
            # Changed: Use watching_percentage instead of watch_percentage
            continue_watching = MovieWatchHistory.objects(
                username=username,
                watching_percentage__gt=0,   # Only show movies user manually set
                watching_percentage__lt=100  # Not completed (100%)
            ).order_by('-last_watched')[:10]  # Most recent 10
            
            if not continue_watching:
                return Response({
                    "username": username,
                    "count": 0,
                    "movies": []
                })
            
            # Build response with movie details
            movies_data = []
            for watch_record in continue_watching:
                try:
                    # Get movie details from Movie OR TVShow collection
                    movie = Movie.objects(id=ObjectId(watch_record.movie_id)).first()
                    
                    # If not found in Movie, try TVShow
                    if not movie:
                        from movies.models import TVShow
                        movie = TVShow.objects(id=ObjectId(watch_record.movie_id)).first()
                    
                    if movie:
                        movies_data.append({
                            "id": str(movie.id),
                            "show_id": getattr(movie, 'show_id', ''),
                            "title": movie.title,
                            "type": getattr(movie, 'type', 'Movie'),
                            "release_year": movie.release_year,
                            "director": getattr(movie, 'director', ''),
                            "cast": getattr(movie, 'cast', ''),
                            "country": getattr(movie, 'country', ''),
                            "rating": getattr(movie, 'rating', ''),
                            "duration": getattr(movie, 'duration', ''),
                            "listed_in": getattr(movie, 'listed_in', ''),
                            "description": getattr(movie, 'description', ''),
                            "poster": getattr(movie, 'poster', None),
                            "imdb_rating": getattr(movie, 'imdb_rating', 0.0),
                            "imdb_votes": getattr(movie, 'imdb_votes', 0),
                            "watch_percentage": round(watch_record.watching_percentage, 1),  # Use watching_percentage
                            "watching_percentage": watch_record.watching_percentage,  # User-editable field
                            "last_watched": watch_record.last_watched
                        })
                except Exception as e:
                    print(f"Error fetching movie {watch_record.movie_id}: {e}")
                    continue
            
            return Response({
                "username": username,
                "count": len(movies_data),
                "movies": movies_data
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e),
                "username": username,
                "count": 0,
                "movies": []
            }, status=400)


class UpdateWatchingPercentageView(APIView):
    """
    Update user-editable watching_percentage for a movie
    Allows users to manually set their watch progress
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        movie_id = request.data.get('movie_id')
        watching_percentage = request.data.get('watching_percentage')
        
        if not username or not movie_id or watching_percentage is None:
            return Response({
                "error": "username, movie_id, and watching_percentage required"
            }, status=400)
        
        # Validate percentage
        try:
            watching_percentage = int(watching_percentage)
            if watching_percentage < 0 or watching_percentage > 100:
                return Response({
                    "error": "watching_percentage must be between 0 and 100"
                }, status=400)
        except ValueError:
            return Response({
                "error": "watching_percentage must be a number"
            }, status=400)
        
        try:
            from .analytics_models import MovieWatchHistory
            
            # Find or create the movie watch history record
            try:
                movie_watch = MovieWatchHistory.objects.get(
                    username=username,
                    movie_id=movie_id
                )
                old_percentage = movie_watch.watching_percentage
                movie_watch.watching_percentage = watching_percentage
                movie_watch.save()
                
                # ✅ AUTO-REGENERATE: If user completes movie OR makes significant progress
                should_regenerate = False
                
                # ✅ NEW: IMMEDIATELY regenerate when completing a movie (85%+)
                # This is the user's CURRENT MOOD showing what they want to watch!
                if watching_percentage >= 85:
                    should_regenerate = True
                    print(f"🔥 User {username} COMPLETED movie - immediate regeneration!")
                
                # Started watching (added to Continue Watching)
                elif old_percentage < 5 and watching_percentage >= 5:
                    should_regenerate = True
                    print(f"🔄 User {username} started watching - will regenerate recommendations")
                
                # Significant progress (every 25%)
                elif watching_percentage // 25 != old_percentage // 25:
                    should_regenerate = True
                    print(f"🔄 User {username} watching progress changed - will regenerate recommendations")
                
                if should_regenerate:
                    try:
                        from recommendations.personalized_sections_engine import PersonalizedSectionsEngine
                        engine = PersonalizedSectionsEngine()
                        
                        # Mark for regeneration
                        from .analytics_models import UserPersonalizedSections
                        sections = UserPersonalizedSections.objects(username=username).first()
                        if sections:
                            sections.needs_update = True
                            sections.save()
                        
                        # Regenerate in background
                        import threading
                        thread = threading.Thread(
                            target=engine.generate_sections_for_user,
                            args=(username, True)
                        )
                        thread.daemon = True
                        thread.start()
                        
                        print(f"✅ Started background regeneration for {username}")
                    except Exception as e:
                        print(f"⚠️  Could not trigger regeneration: {e}")
                
                return Response({
                    "success": True,
                    "message": "Watching percentage updated successfully",
                    "movie_id": movie_id,
                    "watching_percentage": watching_percentage,
                    "regenerated": should_regenerate
                })
            except MovieWatchHistory.DoesNotExist:
                # If no watch history exists, create one
                from movies.models import Movie, TVShow
                
                # Try to get movie details
                movie = None
                try:
                    from bson import ObjectId
                    movie = Movie.objects.get(id=ObjectId(movie_id))
                except:
                    try:
                        movie = TVShow.objects.get(id=ObjectId(movie_id))
                    except:
                        return Response({
                            "error": "Movie not found"
                        }, status=404)
                
                # Create new watch history record
                movie_watch = MovieWatchHistory(
                    username=username,
                    movie_id=movie_id,
                    movie_title=movie.title,
                    movie_type=movie.type if hasattr(movie, 'type') else 'Movie',
                    watching_percentage=watching_percentage,
                    genres=[g.strip() for g in movie.listed_in.split(',')] if hasattr(movie, 'listed_in') and movie.listed_in else []
                )
                movie_watch.save()
                
                # ✅ NEW ACTIVITY: Trigger regeneration
                if watching_percentage >= 5:
                    try:
                        from recommendations.personalized_sections_engine import PersonalizedSectionsEngine
                        engine = PersonalizedSectionsEngine()
                        
                        # Mark for regeneration
                        from .analytics_models import UserPersonalizedSections
                        sections = UserPersonalizedSections.objects(username=username).first()
                        if sections:
                            sections.needs_update = True
                            sections.save()
                        
                        # Regenerate in background
                        import threading
                        thread = threading.Thread(
                            target=engine.generate_sections_for_user,
                            args=(username, True)
                        )
                        thread.daemon = True
                        thread.start()
                        
                        print(f"✅ User {username} added new movie to Continue Watching - regenerating")
                    except Exception as e:
                        print(f"⚠️  Could not trigger regeneration: {e}")
                
                return Response({
                    "success": True,
                    "message": "Watch history created with watching percentage",
                    "movie_id": movie_id,
                    "watching_percentage": watching_percentage,
                    "regenerated": watching_percentage >= 5
                })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e)
            }, status=500)
