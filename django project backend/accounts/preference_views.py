"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 USER PREFERENCES API VIEWS  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    API endpoints for managing user genre preferences
    
    ✅ FIX: When user changes genres, AUTOMATICALLY regenerate recommendations!
    
    ENDPOINTS:
    - POST /api/preferences/update/ → Update user's favorite genres
    - GET /api/preferences/<username>/ → Get user's preferences

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from accounts.analytics_models import UserPreferences, UserPersonalizedSections
from datetime import datetime


class UpdateUserPreferencesView(APIView):
    """
    Update user's favorite genres and AUTO-REGENERATE recommendations
    
    ✅ FIX: When genres change, mark sections for immediate regeneration!
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            new_genres = request.data.get('favorite_genres', [])
            
            if not username:
                return Response({
                    "error": "username is required"
                }, status=400)
            
            if not new_genres or len(new_genres) == 0:
                return Response({
                    "error": "favorite_genres is required (must be a list)"
                }, status=400)
            
            print(f"\n{'='*80}")
            print(f"🔄 UPDATING PREFERENCES FOR: {username}")
            print(f"{'='*80}")
            print(f"New genres: {new_genres}")
            
            # Get or create UserPreferences
            try:
                prefs = UserPreferences.objects.get(username=username)
                old_genres = prefs.favorite_genres or []
                print(f"Old genres: {old_genres}")
            except UserPreferences.DoesNotExist:
                prefs = UserPreferences(username=username)
                old_genres = []
                print(f"Creating new preferences (user had none)")
            
            # Update genres
            prefs.favorite_genres = new_genres
            prefs.updated_at = datetime.utcnow()
            prefs.last_activity = datetime.utcnow()
            prefs.save()
            
            print(f"✅ Preferences updated successfully")
            
            # ✅ FIX: Check if genres changed significantly
            genres_changed = set(new_genres[:3]) != set(old_genres[:3])
            
            if genres_changed:
                print(f"⚠️  GENRES CHANGED! Marking sections for regeneration...")
                
                # Mark personalized sections for immediate regeneration
                try:
                    sections = UserPersonalizedSections.objects(username=username).first()
                    if sections:
                        sections.needs_update = True
                        sections.save()
                        print(f"✅ Sections marked for regeneration")
                    else:
                        print(f"ℹ️  No sections exist yet (will be generated on next load)")
                except Exception as e:
                    print(f"⚠️  Could not mark sections: {e}")
                
                # ✅ OPTIONAL: Regenerate sections immediately in background
                try:
                    from recommendations.personalized_sections_engine import PersonalizedSectionsEngine
                    engine = PersonalizedSectionsEngine()
                    
                    print(f"🔄 Regenerating sections immediately...")
                    engine.generate_sections_for_user(username, force_regenerate=True)
                    print(f"✅ Sections regenerated successfully!")
                    
                except Exception as e:
                    print(f"⚠️  Could not regenerate sections immediately: {e}")
            else:
                print(f"ℹ️  No significant genre changes detected")
            
            print(f"{'='*80}\n")
            
            return Response({
                "success": True,
                "message": "Preferences updated successfully",
                "genres_changed": genres_changed,
                "favorite_genres": new_genres
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e)
            }, status=500)


class GetUserPreferencesView(APIView):
    """
    Get user's current preferences
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            prefs = UserPreferences.objects.get(username=username)
            
            return Response({
                "username": username,
                "favorite_genres": prefs.favorite_genres or [],
                "total_movies_watched": prefs.total_movies_watched or 0,
                "total_movies_liked": prefs.total_movies_liked or 0,
                "total_searches": prefs.total_searches or 0,
                "last_activity": prefs.last_activity,
                "updated_at": prefs.updated_at
            })
            
        except UserPreferences.DoesNotExist:
            return Response({
                "username": username,
                "favorite_genres": [],
                "total_movies_watched": 0,
                "total_movies_liked": 0,
                "total_searches": 0,
                "message": "No preferences found for this user"
            })
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=500)
