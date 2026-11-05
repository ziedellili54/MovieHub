import uuid
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Favorite
from movies.models import Movie


class CustomLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = str(request.data.get("username") or "").strip()
        password = str(request.data.get("password") or "").strip()

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=400)

        user = None
        try:
            # Support username or email login (case-insensitive)
            if "@" in username:
                user = User.objects(email__iexact=username).first()
            else:
                user = User.objects(username__iexact=username).first()
        except Exception:
            user = None

        if user:
            if user.check_password(password):
                refresh = RefreshToken()
                refresh["username"] = user.username
                refresh["user_id"] = str(user.id)

                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "username": user.username,
                    "user_id": str(user.id),
                    "role": "admin" if user.username.lower() == "admin" else "user"
                }, status=200)

        # Fallback to Django auth standard user table (e.g. SQLite superusers)
        from django.contrib.auth import authenticate
        django_user = authenticate(username=username, password=password)
        if django_user:
            refresh = RefreshToken()
            refresh["username"] = django_user.username
            refresh["user_id"] = str(django_user.id)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": django_user.username,
                "user_id": str(django_user.id),
                "role": "admin" if django_user.is_superuser or django_user.username.lower() == "admin" else "user"
            }, status=200)

        return Response({"error": "Invalid credentials"}, status=401)


class CustomRegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        email = str(request.data.get("email", "")).strip()
        password = str(request.data.get("password", "")).strip()
        confirm_password = str(request.data.get("confirm_password", "")).strip()

        if not username or not email or not password or not confirm_password:
            return Response({"error": "All fields are required"}, status=400)

        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        if User.objects(username__iexact=username).first():
            return Response({"error": "Username already exists"}, status=400)

        if User.objects(email__iexact=email).first():
            return Response({"error": "Email already registered"}, status=400)

        user_id = str(uuid.uuid4())[:8]
        user = User(username=username, email=email, user_id=user_id)
        user.set_password(password)
        user.save()

        import json
        import os
        from django.conf import settings
        profiles_dir = os.path.join(settings.BASE_DIR, 'user_profiles')
        os.makedirs(profiles_dir, exist_ok=True)
        profile_path = os.path.join(profiles_dir, f"{username}_profile.json")
        with open(profile_path, 'w') as f:
            json.dump({
                "user_id": user_id,
                "username": username,
                "email": email,
                "password_hash": user.password
            }, f, indent=4)

        return Response({"message": "Registration successful", "user_id": user_id}, status=201)


def login_page(request):
    if request.session.get("username"):
        if request.session.get("username") == "admin":
            return redirect("admin_dashboard")
        return redirect("movies_page")

    if request.method == "POST":
        login_identifier = str(request.POST.get("username", "")).strip()
        password = str(request.POST.get("password", "")).strip()

        try:
            if "@" in login_identifier:
                user = User.objects(email__iexact=login_identifier).first()
            else:
                user = User.objects(username__iexact=login_identifier).first()
            
            if user and user.check_password(password):
                request.session["username"] = user.username
                if user.username.lower() == "admin":
                    return redirect("admin_dashboard")
                return redirect("movies_page")
            else:
                return render(request, "accounts/login.html", {"error": "Invalid credentials"})
        except Exception:
            return render(request, "accounts/login.html", {"error": "User not found"})

    return render(request, "accounts/login.html")


def register_page(request):
    if request.method == "POST":
        username = str(request.POST.get("username", "")).strip()
        email = str(request.POST.get("email", "")).strip()
        password = str(request.POST.get("password", "")).strip()
        confirm_password = str(request.POST.get("confirm_password", "")).strip()

        if not username or not email or not password or not confirm_password:
            return render(request, "accounts/register.html", {"error": "All fields are required"})

        if password != confirm_password:
            return render(request, "accounts/register.html", {"error": "Passwords do not match"})

        if User.objects(username__iexact=username).first():
            return render(request, "accounts/register.html", {"error": "Username already exists"})

        if User.objects(email__iexact=email).first():
            return render(request, "accounts/register.html", {"error": "Email already registered"})

        user_id = str(uuid.uuid4())[:8]
        user = User(username=username, email=email, user_id=user_id)
        user.set_password(password)
        user.save()

        import json
        import os
        from django.conf import settings
        profiles_dir = os.path.join(settings.BASE_DIR, 'user_profiles')
        os.makedirs(profiles_dir, exist_ok=True)
        profile_path = os.path.join(profiles_dir, f"{username}_profile.json")
        with open(profile_path, 'w') as f:
            json.dump({
                "user_id": user_id,
                "username": username,
                "email": email,
                "password_hash": user.password
            }, f, indent=4)

        return redirect("login_page")

    return render(request, "accounts/register.html")


def admin_login_page(request):
    if request.session.get("username") == "admin":
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = str(request.POST.get("username", "")).strip()
        password = str(request.POST.get("password", "")).strip()

        try:
            user = User.objects(username__iexact=username).first()
            if user and user.username.lower() == "admin" and user.check_password(password):
                request.session["username"] = "admin"
                return redirect("admin_dashboard")
            else:
                return render(request, "accounts/admin_login.html", {"error": "Invalid credentials or unauthorized"})
        except Exception:
            return render(request, "accounts/admin_login.html", {"error": "Invalid credentials or unauthorized"})

    return render(request, "accounts/admin_login.html")


def logout_view(request):
    request.session.flush()
    return redirect("login_page")


def admin_dashboard(request):
    if request.session.get("username") != "admin":
        return redirect("admin_login")

    movies = Movie.objects.all()
    users = User.objects.all()

    return render(request, "accounts/admin_dashboard.html", {
        "movies": movies,
        "users": users
    })


def delete_movie(request, movie_id):
    if request.session.get("username") != "admin":
        return redirect("admin_login")

    try:
        movie = Movie.objects.get(id=movie_id)
        movie.delete()
    except Movie.DoesNotExist:
        pass

    return redirect("admin_dashboard")


def edit_movie(request, movie_id):
    if request.session.get("username") != "admin":
        return redirect("admin_login")

    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return redirect("admin_dashboard")

    if request.method == "POST":
        movie.title = request.POST.get("title", "").strip()
        movie.type = request.POST.get("type", "").strip()
        try:
            movie.release_year = int(request.POST.get("release_year"))
        except (ValueError, TypeError):
            pass
        movie.director = request.POST.get("director", "").strip()
        movie.cast = request.POST.get("cast", "").strip()
        movie.country = request.POST.get("country", "").strip()
        movie.listed_in = request.POST.get("listed_in", "").strip()
        movie.description = request.POST.get("description", "").strip()
        movie.save()
        return redirect("admin_dashboard")

    return render(request, "movies/edit_movie.html", {"movie": movie})


def delete_user(request, user_id):
    if request.session.get("username") != "admin":
        return redirect("admin_login")

    try:
        user = User.objects.get(id=user_id)
        if user.username != "admin":
            user.delete()
    except User.DoesNotExist:
        pass
    return redirect("admin_dashboard")


class ListUsersView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        users = User.objects.all()
        data = []
        for user in users:
            # Check if role field exists, otherwise default to 'user'
            role = 'user'  # default
            
            # Try to get role from document
            if hasattr(user, 'role'):
                role = user.role if user.role else 'user'
            elif hasattr(user, 'is_admin') and user.is_admin == 'true':
                role = 'admin'
            elif user.username == 'admin':
                role = 'admin'
            
            data.append({
                "id": str(user.id),
                "user_id": user.user_id if hasattr(user, 'user_id') else None,
                "username": user.username,
                "email": user.email if hasattr(user, 'email') else None,
                "role": role
            })
        return Response({"users": data})


class DeleteUserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            if user.username == "admin":
                return Response({"error": "Cannot delete system administrator"}, status=400)
            user.delete()
            return Response({"message": "User deleted successfully"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class FavoritesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):
        favs = Favorite.objects.filter(username=username)
        movie_ids = [f.movie_id for f in favs]
        return Response({"username": username, "favorites": movie_ids})

    def post(self, request, username):
        movie_id = request.data.get("movie_id")
        if not movie_id:
            return Response({"error": "movie_id is required"}, status=400)
        
        fav = Favorite.objects.filter(username=username, movie_id=str(movie_id)).first()
        if fav:
            fav.delete()
            is_fav = False
        else:
            Favorite(username=username, movie_id=str(movie_id)).save()
            is_fav = True
        
        # ✅ MARK SECTIONS AS NEEDING UPDATE when favorites change
        try:
            from recommendations.personalized_sections_engine import PersonalizedSectionsEngine
            engine = PersonalizedSectionsEngine()
            engine.mark_sections_for_update(username, reason='favorites_changed')
        except Exception as e:
            print(f"Error marking sections for update: {e}")
            
        favs = Favorite.objects.filter(username=username)
        return Response({"username": username, "is_favorite": is_fav, "favorites": [f.movie_id for f in favs]})


class FavoriteMoviesView(APIView):
    """Return full movie details for a user's favorites"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):
        from movies.models import Movie, TVShow
        
        favs = Favorite.objects.filter(username=username)
        movie_ids = [f.movie_id for f in favs]
        
        if not movie_ids:
            return Response({"username": username, "movies": [], "count": 0})
        
        # Fetch movies and TV shows by their IDs
        movies_data = []
        for movie_id in movie_ids:
            # Try Movie collection first
            item = Movie.objects(id=movie_id).first()
            if not item:
                # Try TVShow collection
                item = TVShow.objects(id=movie_id).first()
            
            if item:
                movies_data.append({
                    "id": str(item.id),
                    "show_id": getattr(item, 'show_id', ''),
                    "title": item.title,
                    "type": getattr(item, 'type', 'Movie'),
                    "release_year": item.release_year,
                    "director": getattr(item, 'director', ''),
                    "cast": getattr(item, 'cast', ''),
                    "country": getattr(item, 'country', ''),
                    "rating": getattr(item, 'rating', ''),
                    "duration": getattr(item, 'duration', ''),
                    "listed_in": getattr(item, 'listed_in', ''),
                    "description": getattr(item, 'description', ''),
                    "poster": getattr(item, 'poster', None)
                })
        
        # Sort by title
        movies_data.sort(key=lambda x: (x["title"] or "").lower())
        
        return Response({
            "username": username,
            "movies": movies_data,
            "count": len(movies_data)
        })


# ══════════════════════════════════════════════════════════════
#  WATCH PROGRESS ENDPOINTS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
def get_watch_progress(request):
    """Get all watch progress for a user"""
    username = request.GET.get('username')
    if not username:
        return Response({'error': 'Username required'}, status=400)
    
    try:
        from .models import WatchProgress
        progress_list = WatchProgress.objects(username=username)
        
        progress_dict = {}
        for prog in progress_list:
            progress_dict[prog.movie_id] = {
                'progress': prog.progress_percentage,
                'watching_percentage': prog.watching_percentage if hasattr(prog, 'watching_percentage') else 0,
                'last_watched': prog.last_watched_at
            }
        
        return Response({'progress': progress_dict})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def update_watch_progress(request):
    """Update watch progress for a specific movie"""
    username = request.data.get('username')
    movie_id = request.data.get('movie_id')
    progress = request.data.get('progress', 0)
    watching_percentage = request.data.get('watching_percentage', None)
    
    if not username or not movie_id:
        return Response({'error': 'Username and movie_id required'}, status=400)
    
    try:
        from .models import WatchProgress
        from datetime import datetime
        
        # Validate progress value
        progress = int(progress)
        if progress < 0:
            progress = 0
        if progress > 100:
            progress = 100
        
        # Validate watching_percentage if provided
        update_fields = {
            'progress_percentage': progress,
            'last_watched_at': datetime.utcnow().isoformat()
        }
        
        if watching_percentage is not None:
            watching_percentage = int(watching_percentage)
            if watching_percentage < 0:
                watching_percentage = 0
            if watching_percentage > 100:
                watching_percentage = 100
            update_fields['watching_percentage'] = watching_percentage
        
        # Update or create progress record
        WatchProgress.objects(username=username, movie_id=movie_id).update_one(
            **{f'set__{k}': v for k, v in update_fields.items()},
            upsert=True
        )
        
        # Track this in analytics for AI recommendations
        if watching_percentage is not None and watching_percentage > 0:
            try:
                from accounts.analytics_models import UserActivity
                from movies.models import Movie, TVShow
                
                # Get movie details
                movie = None
                try:
                    movie = Movie.objects.get(id=movie_id)
                except:
                    try:
                        movie = TVShow.objects.get(id=movie_id)
                    except:
                        pass
                
                if movie:
                    # Create activity for AI tracking
                    UserActivity(
                        username=username,
                        activity_type='movie_watch',
                        movie_id=movie_id,
                        movie_title=movie.title,
                        genres=[g.strip() for g in (movie.listed_in or '').split(',') if g.strip()],
                        watch_duration_seconds=0,
                        watch_percentage=watching_percentage,
                        timestamp=datetime.utcnow()  # Use timestamp, not watched_at
                    ).save()
            except Exception as e:
                print(f"Warning: Could not track activity for AI: {e}")
        
        response_data = {
            'message': 'Progress updated',
            'progress': progress
        }
        if watching_percentage is not None:
            response_data['watching_percentage'] = watching_percentage
        
        return Response(response_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
