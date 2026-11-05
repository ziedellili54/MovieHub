"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 MOVIEHUB - URL ROUTING CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    This file maps URLs to view functions. When a request comes in, Django checks
    this file to find which function should handle it.

EXAMPLE FLOW:
    User visits: http://localhost:8000/api/movies/
    Django checks urlpatterns → finds path('api/movies/', ListMoviesView)
    Django calls ListMoviesView → Returns JSON response

TOTAL ROUTES: 44
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT USER MANAGEMENT VIEWS
# File: accounts/views.py
# Purpose: Authentication, user CRUD, favorites, watch progress
# ═══════════════════════════════════════════════════════════════════════════
from accounts.views import (
    CustomLoginView,          # JWT login API (returns tokens)
    CustomRegisterView,       # User registration API
    login_page,               # HTML login form (session-based)
    register_page,            # HTML registration form
    admin_dashboard,          # Admin panel HTML page
    delete_movie,             # Delete movie (admin, HTML)
    edit_movie,               # Edit movie (admin, HTML)
    delete_user,              # Delete user (admin, HTML)
    admin_login_page,         # Admin login HTML form
    logout_view,              # Logout and clear session
    ListUsersView,            # API: Get all users
    DeleteUserView,           # API: Delete user by ID
    FavoritesView,            # API: Get/toggle favorites
    FavoriteMoviesView,       # API: Get favorite movie details
    get_watch_progress,       # API: Get watch progress (0-100%)
    update_watch_progress     # API: Update watch progress
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT PASSWORD RESET VIEWS
# File: accounts/password_reset_views.py
# Purpose: Password reset with email verification
# ═══════════════════════════════════════════════════════════════════════════
from accounts.password_reset_views import (
    RequestPasswordResetView,  # API: Request password reset code
    VerifyCodeView,            # API: Verify reset code
    ResetPasswordView          # API: Reset password with code
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT ANALYTICS VIEWS
# File: accounts/analytics_views.py
# Purpose: Track user behavior (searches, watches, sessions)
# ═══════════════════════════════════════════════════════════════════════════
from accounts.analytics_views import (
    TrackActivityView,        # API: Log any user activity
    StartSessionView,         # API: Start session when app opens
    EndSessionView,           # API: End session when app closes
    GetUserAnalyticsView,     # API: Get analytics for one user
    GetAllUsersAnalyticsView,  # API: Get analytics for all users (admin)
    GetUserMovieWatchPercentagesView,  # API: Get per-movie watch percentages
    GetMovieWatchDetailsView,  # API: Get detailed watch sessions for a movie
    GetContinueWatchingView,   # API: Get Continue Watching list
    UpdateWatchingPercentageView  # API: Update user-editable watching percentage
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT RECOMMENDATION FEEDBACK VIEWS (NEW - AI SELF-LEARNING)
# File: accounts/recommendation_feedback_views.py
# Purpose: Track AI recommendation performance for self-improvement
# ═══════════════════════════════════════════════════════════════════════════
from accounts.recommendation_feedback_views import (
    TrackRecommendationFeedbackView,  # API: Track which recommendations users click
    GetRecommendationStatsView         # API: Get AI performance statistics
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT PREFERENCE VIEWS (UPDATE USER GENRES)
# File: accounts/preference_views.py
# Purpose: Update user's favorite genres and auto-regenerate recommendations
# ═══════════════════════════════════════════════════════════════════════════
from accounts.preference_views import (
    UpdateUserPreferencesView,  # API: Update user's favorite genres
    GetUserPreferencesView       # API: Get user's current preferences
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT DISLIKE VIEWS (NEW - HIDDEN DISLIKES WITH AI IMPACT)
# File: accounts/dislike_views.py
# Purpose: Hidden dislike system that filters content and penalizes AI
# ═══════════════════════════════════════════════════════════════════════════
from accounts.dislike_views import (
    DislikeMovieView,      # API: Dislike a movie (hidden, affects AI)
    GetDislikesView,       # API: Get all dislikes (admin/debug)
    RemoveDislikeView      # API: Remove dislike (allow movie again)
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT MOVIE MANAGEMENT VIEWS
# File: movies/views.py
# Purpose: Movie CRUD, search, external API integration, packs
# ═══════════════════════════════════════════════════════════════════════════
from movies.views import (
    FetchMoviesView,          # API: Fetch movies from RapidAPI
    ListMoviesView,           # API: List movies (pagination, filters)
    AddMovieView,             # API: Add new movie
    DeleteMovieView,          # API: Delete movie
    EditMovieView,            # API: Edit movie
    fetch_page,               # HTML: Form to fetch movies
    movies_page,              # HTML: Display all movies
    fetch_all_years_page,     # HTML: Fetch movies for all years
    search_movie_page,        # HTML: Search movies form
    add_searched_movie,       # HTML: Add movie from search
    add_movie_page,           # HTML: Manual add movie form
    api_search_and_save,      # HTML: Search OMDb and save
    test_simple_view,         # Simple test route
    GenresView,               # API: Get all genres
    ApiSearchOMDbView,        # API: Search OMDb for movies
    ApiSaveSelectedOMDbView,  # API: Save selected OMDb results
    ExternalApiBrowseView,    # API: Fetch from any external API
    PackPreviewView,          # API: Preview pack before creating
    PackListView,             # API: List/create movie packs
    PackDetailView            # API: Get/update/delete specific pack
)


# ═══════════════════════════════════════════════════════════════════════════
# URL PATTERNS - ROUTES ALL REQUESTS TO APPROPRIATE VIEWS
# ═══════════════════════════════════════════════════════════════════════════
urlpatterns = [
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📋 ADMIN PANEL ROUTES (HTML Pages - Session Authentication)
    # Purpose: Admin dashboard for managing movies and users
    # Auth: Requires session with username="admin"
    # Returns: HTML pages (templates)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('admin/', admin_dashboard, name='admin_dashboard'),
    # GET /admin/ → Shows admin dashboard with all movies and users
    # Function: admin_dashboard() in accounts/views.py
    # Template: templates/accounts/admin_dashboard.html
    
    path('admin/login/', admin_login_page, name='admin_login'),
    # GET/POST /admin/login/ → Admin login form
    # Function: admin_login_page() in accounts/views.py
    # Creates session cookie, no JWT tokens
    # Template: templates/accounts/admin_login.html
    
    path('admin/delete-movie/<str:movie_id>/', delete_movie, name='delete_movie'),
    # POST /admin/delete-movie/abc123/ → Deletes movie by ID
    # <str:movie_id> captures the ID from URL
    # Function: delete_movie() in accounts/views.py
    # Redirects back to admin dashboard after deletion
    
    path('admin/edit-movie/<str:movie_id>/', edit_movie, name='edit_movie'),
    # GET/POST /admin/edit-movie/abc123/ → Edit movie form
    # Function: edit_movie() in accounts/views.py
    # Template: templates/movies/edit_movie.html
    
    path('admin/delete-user/<str:user_id>/', delete_user, name='delete_user'),
    # POST /admin/delete-user/xyz789/ → Deletes user (can't delete admin)
    # Function: delete_user() in accounts/views.py
    # Redirects back to admin dashboard
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 👤 USER PAGES (HTML Pages - Session Authentication)
    # Purpose: Regular user login and registration
    # Auth: Session-based (creates session cookie)
    # Returns: HTML pages
    # ═══════════════════════════════════════════════════════════════════════
    
    path('user/', login_page, name='login_page'),
    # GET/POST /user/ → User login form
    # Function: login_page() in accounts/views.py
    # Template: templates/accounts/login.html
    
    path('user/register/', register_page, name='register_page'),
    # GET/POST /user/register/ → User registration form
    # Function: register_page() in accounts/views.py
    # Template: templates/accounts/register.html
    
    path('logout/', logout_view, name='logout'),
    # GET /logout/ → Logs out user (clears session)
    # Function: logout_view() in accounts/views.py
    # Redirects to login page
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔐 AUTHENTICATION API (JSON - JWT Tokens)
    # Purpose: API login/register for Angular frontend
    # Auth: Returns JWT tokens (access + refresh)
    # Returns: JSON responses
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/login/', CustomLoginView.as_view(), name='custom_login'),
    # POST /api/login/ → JWT login
    # Body: {username, password}
    # Response: {access, refresh, username, user_id, role}
    # Function: CustomLoginView.post() in accounts/views.py
    # Used by Angular frontend
    
    path('api/register/', CustomRegisterView.as_view(), name='custom_register'),
    # POST /api/register/ → Create new user account
    # Body: {username, email, password, confirm_password}
    # Response: {message, user_id}
    # Function: CustomRegisterView.post() in accounts/views.py
    # Saves to MongoDB 'users' collection
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔑 PASSWORD RESET API (JSON - Email Verification)
    # Purpose: Allow users to reset forgotten passwords via email
    # Auth: No authentication required (public endpoints)
    # Returns: JSON responses
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/password-reset/request/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    # POST /api/password-reset/request/ → Request password reset code
    # Body: {email: "user@example.com"}
    # Response: {success: true, message: "Code sent to email"}
    # Function: RequestPasswordResetView.post() in password_reset_views.py
    # Sends 6-digit verification code via email
    
    path('api/password-reset/verify-code/', VerifyCodeView.as_view(), name='verify_reset_code'),
    # POST /api/password-reset/verify-code/ → Verify the code
    # Body: {email: "user@example.com", code: "123456"}
    # Response: {success: true, username: "john"}
    # Function: VerifyCodeView.post() in password_reset_views.py
    
    path('api/password-reset/reset/', ResetPasswordView.as_view(), name='reset_password'),
    # POST /api/password-reset/reset/ → Reset password with verified code
    # Body: {email: "user@example.com", code: "123456", new_password: "newpass123"}
    # Response: {success: true, message: "Password reset successful"}
    # Function: ResetPasswordView.post() in password_reset_views.py
    # Updates password in MongoDB
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎬 MOVIES API (JSON)
    # Purpose: Movie CRUD operations and external API integration
    # Auth: JWT tokens (some endpoints allow anonymous)
    # Returns: JSON responses
    # Related Models: Movie, TVShow (movies/models.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/movies/fetch/', FetchMoviesView.as_view(), name='fetch_movies'),
    # POST /api/movies/fetch/ → Fetch movies from RapidAPI
    # Body: {year: "2023", type: "Movie"}
    # Response: {message, count}
    # Function: FetchMoviesView.post() in movies/views.py
    # Saves fetched movies to MongoDB 'movies' or 'tv_shows' collection
    
    path('api/movies/', ListMoviesView.as_view(), name='list_movies'),
    # GET /api/movies/?limit=24&page=1&search=action&genre=Action&sort=year-desc
    # → List movies with pagination, search, filters, sorting
    # Query Params: limit, page, search, type, genre, sort
    # Response: {movies: [...], count, total, page, limit}
    # Function: ListMoviesView.get() in movies/views.py
    # Searches both 'movies' and 'tv_shows' collections
    
    path('api/movies/add/', AddMovieView.as_view(), name='add_movie'),
    # POST /api/movies/add/ → Manually add a new movie
    # Body: {title, type, release_year, director, cast, ...}
    # Response: {message, id}
    # Function: AddMovieView.post() in movies/views.py
    
    path('api/movies/delete/<str:movie_id>/', DeleteMovieView.as_view(), name='api_delete_movie'),
    # DELETE /api/movies/delete/abc123/ → Delete movie by ID
    # Function: DeleteMovieView.delete() in movies/views.py
    # Removes from MongoDB
    
    path('api/movies/edit/<str:movie_id>/', EditMovieView.as_view(), name='api_edit_movie'),
    # PUT /api/movies/edit/abc123/ → Update movie details
    # Body: {title, release_year, director, ...}
    # Function: EditMovieView.put() in movies/views.py
    
    path('api/genres/', GenresView.as_view(), name='api_genres'),
    # GET /api/genres/ → Get all unique genres
    # Response: {genres: ["Action", "Drama", ...]}
    # Function: GenresView.get() in movies/views.py
    # Extracts from 'listed_in' field, splits by comma
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 👥 USER MANAGEMENT API (JSON)
    # Purpose: Admin operations to manage users
    # Auth: JWT tokens (admin only)
    # Related Model: User (accounts/models.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/users/', ListUsersView.as_view(), name='api_list_users'),
    # GET /api/users/ → List all users
    # Response: {users: [{id, user_id, username, email, role}, ...]}
    # Function: ListUsersView.get() in accounts/views.py
    
    path('api/users/delete/<str:user_id>/', DeleteUserView.as_view(), name='api_delete_user'),
    # DELETE /api/users/delete/xyz789/ → Delete user (can't delete admin)
    # Function: DeleteUserView.delete() in accounts/views.py
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # ❤️ FAVORITES API (JSON)
    # Purpose: User favorites system
    # Auth: JWT tokens
    # Related Model: Favorite (accounts/models.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/favorites/<str:username>/', FavoritesView.as_view(), name='api_favorites'),
    # GET /api/favorites/john/ → Get user's favorite movie IDs
    # Response: {username, favorites: ["abc123", "xyz789", ...]}
    #
    # POST /api/favorites/john/ → Toggle favorite (add/remove)
    # Body: {movie_id: "abc123"}
    # Response: {username, is_favorite: true/false, favorites: [...]}
    # Function: FavoritesView.get()/post() in accounts/views.py
    
    path('api/favorites/<str:username>/movies/', FavoriteMoviesView.as_view(), name='api_favorite_movies'),
    # GET /api/favorites/john/movies/ → Get full movie details for favorites
    # Response: {username, count, movies: [{title, poster, ...}, ...]}
    # Function: FavoriteMoviesView.get() in accounts/views.py
    # Fetches from both 'movies' and 'tv_shows' collections
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # ⏯️ WATCH PROGRESS API (JSON)
    # Purpose: Track how much of a movie user has watched (0-100%)
    # Auth: JWT tokens
    # Related Model: WatchProgress (accounts/models.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/watch-progress/', get_watch_progress, name='api_watch_progress'),
    # GET /api/watch-progress/?username=john → Get all watch progress for user
    # Response: {progress: {movie_id: {progress: 75, last_watched: "2024-..."}, ...}}
    # Function: get_watch_progress() in accounts/views.py
    
    path('api/watch-progress/update/', update_watch_progress, name='api_watch_progress_update'),
    # POST /api/watch-progress/update/ → Update watch progress
    # Body: {username: "john", movie_id: "abc123", progress: 50}
    # Response: {message, progress}
    # Function: update_watch_progress() in accounts/views.py
    # Saves to 'watch_progress' collection
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📊 ANALYTICS API (JSON)
    # Purpose: Track user behavior for analytics dashboard
    # Auth: JWT tokens (some endpoints allow anonymous)
    # Related Models: UserActivity, UserPreferences, UserSession (analytics_models.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/analytics/track/', TrackActivityView.as_view(), name='track_activity'),
    # POST /api/analytics/track/ → Log any user activity
    # Body: {username, activity_type, movie_id, watch_duration_seconds, device_type, ...}
    # Activity types: search, movie_watch, movie_click, like, dislike, etc.
    # Response: {success: true, message}
    # Function: TrackActivityView.post() in analytics_views.py
    # Saves to 'user_activities' + updates 'user_preferences'
    
    path('api/analytics/session/start/', StartSessionView.as_view(), name='start_session'),
    # POST /api/analytics/session/start/ → Start new session when app opens
    # Body: {username, device_type, browser, os, country, ip_address}
    # Response: {success: true, session_id}
    # Function: StartSessionView.post() in analytics_views.py
    # Frontend saves session_id for subsequent requests
    
    path('api/analytics/session/end/', EndSessionView.as_view(), name='end_session'),
    # POST /api/analytics/session/end/ → End session when app closes
    # Body: {session_id}
    # Response: {success: true}
    # Function: EndSessionView.post() in analytics_views.py
    # Calculates session duration_seconds
    
    path('api/analytics/user/<str:username>/', GetUserAnalyticsView.as_view(), name='user_analytics'),
    # GET /api/analytics/user/john/ → Get complete analytics for one user
    # Response: {username, preferences, metrics, recent_activities}
    # Function: GetUserAnalyticsView.get() in analytics_views.py
    # Used for user dashboard
    
    path('api/analytics/all/', GetAllUsersAnalyticsView.as_view(), name='all_users_analytics'),
    # GET /api/analytics/all/ → Get analytics for all users (admin dashboard)
    # Response: {total_users, users: [{username, total_movies_watched, ...}, ...]}
    # Function: GetAllUsersAnalyticsView.get() in analytics_views.py
    
    path('api/analytics/user/<str:username>/movies/', GetUserMovieWatchPercentagesView.as_view(), name='user_movie_percentages'),
    # GET /api/analytics/user/john/movies/ → Get watch percentage for EACH movie user watched
    # Response: {username, total_movies, statistics, movies: [{movie_title, watch_percentage, ...}]}
    # Function: GetUserMovieWatchPercentagesView.get() in analytics_views.py
    
    path('api/analytics/user/<str:username>/movie/<str:movie_id>/', GetMovieWatchDetailsView.as_view(), name='movie_watch_details'),
    # GET /api/analytics/user/john/movie/abc123/ → Get all watch sessions for a specific movie
    # Response: {username, movie_title, summary, watch_sessions: [{timestamp, watch_percentage, ...}]}
    # Function: GetMovieWatchDetailsView.get() in analytics_views.py
    
    path('api/analytics/continue-watching/<str:username>/', GetContinueWatchingView.as_view(), name='continue_watching'),
    # GET /api/analytics/continue-watching/john/ → Get Continue Watching list (5-90% progress)
    # Response: {username, count, movies: [{id, title, poster, watch_percentage, last_watched}, ...]}
    # Function: GetContinueWatchingView.get() in analytics_views.py
    
    path('api/analytics/update-watching-percentage/', UpdateWatchingPercentageView.as_view(), name='update_watching_percentage'),
    # POST /api/analytics/update-watching-percentage/ → Update user-editable watching percentage
    # Body: {username: "john", movie_id: "abc123", watching_percentage: 50}
    # Response: {success: true, message: "Updated", movie_id, watching_percentage}
    # Function: UpdateWatchingPercentageView.post() in analytics_views.py
    
    path('api/analytics/recommendation-feedback/', TrackRecommendationFeedbackView.as_view(), name='track_recommendation_feedback'),
    # POST /api/analytics/recommendation-feedback/ → Track which recommendation user clicked
    # Body: {username, recommendation_batch_id, recommended_movie_id, recommendation_position, similarity_score, ...}
    # Response: {success: true, feedback_score, feedback_category, message}
    # Function: TrackRecommendationFeedbackView.post() in recommendation_feedback_views.py
    # Used by: AI to learn from user behavior (self-improvement)
    
    path('api/analytics/recommendation-stats/<str:username>/', GetRecommendationStatsView.as_view(), name='recommendation_stats'),
    # GET /api/analytics/recommendation-stats/john/ → Get AI performance statistics
    # Response: {total_recommendations_clicked, average_position_clicked, feedback_distribution, ai_performance, ...}
    # Function: GetRecommendationStatsView.get() in recommendation_feedback_views.py
    # Shows how well AI is performing for this user
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # USER PREFERENCES - Update Favorite Genres (✅ AUTO-REGENERATE RECOMMENDATIONS!)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/preferences/update/', UpdateUserPreferencesView.as_view(), name='update_preferences'),
    # POST /api/preferences/update/ → Update user's favorite genres
    # Body: {username: "john", favorite_genres: ["Action", "Comedy", "Sci-Fi"]}
    # Response: {success: true, genres_changed: true, favorite_genres: [...]}
    # Function: UpdateUserPreferencesView.post() in preference_views.py
    # ✅ FIX: Automatically regenerates recommendations when genres change!
    
    path('api/preferences/<str:username>/', GetUserPreferencesView.as_view(), name='get_preferences'),
    # GET /api/preferences/john/ → Get user's current preferences
    # Response: {username, favorite_genres: [...], total_movies_watched, total_searches, ...}
    # Function: GetUserPreferencesView.get() in preference_views.py
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 👎 DISLIKE SYSTEM API (JSON - Hidden Dislikes with AI Impact)
    # Purpose: Allow users to dislike movies, hide them, and penalize AI
    # Auth: JWT tokens (some allow anonymous)
    # Related Model: MovieDislike (analytics_models.py)
    # KEY FEATURE: Dislikes are HIDDEN (not shown like favorites)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/dislikes/', DislikeMovieView.as_view(), name='dislike_movie'),
    # POST /api/dislikes/ → Dislike a movie
    # Body: {username, movie_id, dislike_reason, was_ai_recommendation, recommendation_position}
    # Response: {success: true, message, ai_penalty, genre_penalties}
    # Function: DislikeMovieView.post() in dislike_views.py
    # Effects:
    #   1. Hides movie from recommendations, trending, packs
    #   2. Penalizes AI if it was recommended (-5 to -20 points)
    #   3. Reduces genre scores in user preferences
    #   4. Saves dislike record (hidden from user)
    
    path('api/dislikes/<str:username>/', GetDislikesView.as_view(), name='get_dislikes'),
    # GET /api/dislikes/john/ → Get all disliked movies (admin/debug only)
    # Response: {success: true, total_dislikes, dislikes: [...]}
    # Function: GetDislikesView.get() in dislike_views.py
    # Note: NOT shown in regular user UI (hidden system)
    
    path('api/dislikes/remove/', RemoveDislikeView.as_view(), name='remove_dislike'),
    # DELETE /api/dislikes/remove/ → Remove a dislike (allow movie again)
    # Body: {username, movie_id}
    # Response: {success: true, message}
    # Function: RemoveDislikeView.delete() in dislike_views.py
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🌐 EXTERNAL API INTEGRATION (JSON)
    # Purpose: Fetch movies from OMDb and other external APIs
    # Auth: JWT tokens (some allow anonymous)
    # Uses: OMDb API (key in .env), RapidAPI
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/omdb/search/', ApiSearchOMDbView.as_view(), name='api_omdb_search'),
    # GET /api/omdb/search/?title=batman → Search OMDb for movies
    # Response: {results: [{title, year, poster, already_saved: true/false}, ...]}
    # Function: ApiSearchOMDbView.get() in movies/views.py
    # Checks which movies already exist in database
    
    path('api/omdb/save-selected/', ApiSaveSelectedOMDbView.as_view(), name='api_omdb_save_selected'),
    # POST /api/omdb/save-selected/ → Save selected movies from OMDb
    # Body: {items: [{title, year, director, ...}, ...]}
    # Response: {message, saved: [...], skipped: [...]}
    # Function: ApiSaveSelectedOMDbView.post() in movies/views.py
    # Prevents duplicates
    
    path('api/external/browse/', ExternalApiBrowseView.as_view(), name='api_external_browse'),
    # POST /api/external/browse/ → Fetch movies from ANY external API URL
    # Body: {api_url: "https://api.sampleapis.com/movies/action"}
    # Response: {message, count}
    # Function: ExternalApiBrowseView.post() in movies/views.py
    # Auto-fetches up to 50 pages from provided API
    
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📦 PACKS API (Movie Collections - JSON)
    # Purpose: Create themed movie collections (e.g., "Action Movies 2024")
    # Auth: JWT tokens
    # Related Model: Pack (movies/models.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/packs/', PackListView.as_view(), name='api_packs_list'),
    # GET /api/packs/ → List all movie packs
    # Response: {packs: [{id, name, genres, years, movie_count}, ...]}
    #
    # POST /api/packs/ → Create new pack
    # Body: {name, genres: [...], years: [...], movie_ids: [...], cover_image}
    # Function: PackListView.get()/post() in movies/views.py
    
    path('api/packs/preview/', PackPreviewView.as_view(), name='api_packs_preview'),
    # GET /api/packs/preview/?genres=Action&years=2020,2021 → Preview pack movies
    # Response: {count, movies: [...]}
    # Function: PackPreviewView.get() in movies/views.py
    # Shows which movies match criteria before creating pack
    
    path('api/packs/<str:pack_id>/', PackDetailView.as_view(), name='api_packs_detail'),
    # GET /api/packs/abc123/ → Get pack details with movies
    # PUT /api/packs/abc123/ → Update pack
    # DELETE /api/packs/abc123/ → Delete pack
    # Function: PackDetailView.get()/put()/delete() in movies/views.py

    
    # ═══════════════════════════════════════════════════════════════════════
    # 🤖 AI RECOMMENDATIONS API (JSON)
    # Purpose: AI-powered movie recommendations using ChromaDB + OpenAI
    # Auth: JWT tokens (some allow anonymous)
    # Related Files: recommendations/recommendation_engine.py, recommendations/views.py
    # ═══════════════════════════════════════════════════════════════════════
    
    path('api/recommendations/', include('recommendations.urls')),
    # GET /api/recommendations/health/ → Check recommendation system status
    # POST /api/recommendations/index-movies/ → Index all movies (admin)
    # GET /api/recommendations/{username}/ → Get personalized recommendations
    # GET /api/recommendations/similar/{movie_id}/ → Get similar movies


    # ═══════════════════════════════════════════════════════════════════════
    # 📄 LEGACY HTML ROUTES (Older Template-Based Pages)
    # Purpose: HTML pages for testing and fallback
    # Note: Angular frontend provides better UX for these features
    # ═══════════════════════════════════════════════════════════════════════
    
    path('login/', login_page, name='login_page_alt'),
    # Alternative URL for login page (same as /user/)
    
    path('register/', register_page, name='register_page_alt'),
    # Alternative URL for register page (same as /user/register/)
    
    path('fetch-page/', fetch_page, name='fetch_page'),
    # HTML form to fetch movies from RapidAPI
    
    path('fetch-all/', fetch_all_years_page, name='fetch_all_years_page'),
    # HTML page to fetch movies for all years (1950-2026)
    
    path('movies-page/', movies_page, name='movies_page'),
    # HTML page showing all movies with year filter
    
    path('search-movie/', search_movie_page, name='search_movie_page'),
    # HTML form to search movies in database
    
    path('add-searched-movie/', add_searched_movie, name='add_searched_movie'),
    # Form submission handler (adds movie from search)
    
    path('add-movie-page/', add_movie_page, name='add_movie_page'),
    # HTML form to manually add a movie
    
    path('api-search/', api_search_and_save, name='api_search_and_save'),
    # HTML page to search OMDb and save results
    
    path('test-simple/', test_simple_view, name='test_simple'),
    # Simple test route (returns "routing works" message)
]

# Serve static files in development

# Serve media files in development (posters, uploaded images)
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.conf import settings
    from django.conf.urls.static import static
    import os
    
    # Serve from STATIC_ROOT (where collectstatic puts files)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Also serve from source folder
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 URL NAMING CONVENTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - /admin/*        → Admin panel (HTML, session auth)
    - /user/*         → User pages (HTML, session auth)
    - /api/*          → API endpoints (JSON, JWT auth)
    - /api/movies/*   → Movie operations
    - /api/favorites/* → Favorites system
    - /api/analytics/* → User behavior tracking
    - /*              → Legacy HTML pages

📌 VARIABLE CAPTURE:
    - <str:movie_id>  → Captures movie ID from URL
    - <str:user_id>   → Captures user ID from URL
    - <str:username>  → Captures username from URL
    - <str:pack_id>   → Captures pack ID from URL

📝 HTTP METHODS:
    - GET    → Read data
    - POST   → Create new data
    - PUT    → Update existing data
    - DELETE → Remove data

🔐 AUTHENTICATION TYPES:
    1. Session Auth (HTML pages)
       - Stores session in db.sqlite3
       - Creates session cookie
       - Used by: /admin/*, /user/*
    
    2. JWT Auth (API endpoints)
       - Returns access + refresh tokens
       - Stored in localStorage (frontend)
       - Used by: /api/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""