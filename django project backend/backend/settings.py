"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ DJANGO SETTINGS - Main Configuration File
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    This file configures EVERYTHING for the Django backend:
    - Database connections (MongoDB + SQLite)
    - Security settings (SECRET_KEY, CORS, JWT)
    - Installed apps and middleware
    - Template and static files locations
    - Authentication system

CRITICAL SETTINGS IN THIS FILE:
    1. MongoDB Connection (lines 25-29) - Main database
    2. CORS Configuration (lines 147-166) - Frontend communication
    3. JWT Settings (lines 169-181) - Token authentication
    4. REST Framework (lines 55-59) - API configuration

RELATED FILES:
    - .env → Contains MONGO_URI secret
    - backend/urls.py → Uses JWT auth configured here
    - All models (accounts/models.py, movies/models.py) → Connect to MongoDB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# BASE DIRECTORY - Root folder of Django project
# ═══════════════════════════════════════════════════════════════════════════
# Used to build absolute paths
# Example: BASE_DIR / 'templates' → 'C:\...\backend\templates'
BASE_DIR = Path(__file__).resolve().parent.parent

import os
import mongoengine
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════════════════
# ENVIRONMENT VARIABLES - Load secrets from .env file
# ═══════════════════════════════════════════════════════════════════════════
# Loads .env file containing sensitive data (not committed to Git)
# .env contains: MONGO_URI="mongodb+srv://username:password@cluster..."
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# MONGODB CONNECTION - Main Database Configuration
# ═══════════════════════════════════════════════════════════════════════════
# Connects to MongoDB Atlas (cloud database)
# All models (User, Movie, TVShow, Favorite, etc.) stored here
mongoengine.connect(
    db="MovieApp",  
    # Database name in MongoDB
    # Collections inside: users, movies, tv_shows, favorites, watch_progress, 
    #                     user_activities, user_preferences, user_sessions, packs
    
    host=os.getenv("MONGO_URI"),
    # Connection string from .env file
    # Format: mongodb+srv://username:password@cluster.mongodb.net/
    # os.getenv() keeps sensitive credentials out of code
    
    tlsAllowInvalidCertificates=True
    # Allows SSL/TLS connection even if certificate validation fails
    # Needed for MongoDB Atlas connections in development
    # WARNING: Should be False in production for security
)

# ═══════════════════════════════════════════════════════════════════════════
# SECURITY SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

SECRET_KEY = 'django-insecure-x2dm^@49o57yquan^-+aab0s&(k1^v5k%egir*4sigqsy%icm#'
# Django's secret key - used for:
#   - Cryptographic signing (sessions, cookies, tokens)
#   - Password reset tokens
#   - CSRF protection
# WARNING: Never expose this in production! Use environment variable instead
# Production: SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = True
# Shows detailed error pages with code traceback
# DEBUG = True → Development (shows errors)
# DEBUG = False → Production (hides errors from users)
# WARNING: Must be False in production to prevent information leakage

ALLOWED_HOSTS = []
# List of domain names this Django site can serve
# Empty list = only localhost allowed (development)
# Production example: ['moviehub.com', 'www.moviehub.com']


# ═══════════════════════════════════════════════════════════════════════════
# INSTALLED APPLICATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Django apps that make up this project
INSTALLED_APPS = [
    # ─────────────────────────────────────────────────────────────────────
    # DJANGO BUILT-IN APPS (Core functionality)
    # ─────────────────────────────────────────────────────────────────────
    'django.contrib.admin',
    # Admin panel at /admin/ (though we use custom admin)
    
    'django.contrib.auth',
    # Authentication system (we use for password hashing only)
    # Note: Users stored in MongoDB, not Django's default User model
    
    'django.contrib.contenttypes',
    # Tracks installed models (required by admin)
    
    'django.contrib.sessions',
    # Session management for admin login (stored in SQLite)
    # Regular users use JWT, admin uses sessions
    
    'django.contrib.messages',
    # One-time notification messages ("Movie added successfully")
    
    'django.contrib.staticfiles',
    # Serves static files (CSS, JS, images)
    
    # ─────────────────────────────────────────────────────────────────────
    # THIRD-PARTY APPS (External packages)
    # ─────────────────────────────────────────────────────────────────────
    'rest_framework',
    # Django REST Framework - builds REST APIs
    # Used by: All API views in accounts/views.py, movies/views.py
    
    'rest_framework_simplejwt',
    # JWT token authentication for API
    # Generates and validates access/refresh tokens
    # Used by: CustomLoginView (accounts/views.py)
    
    'corsheaders',
    # Allows Angular frontend (localhost:4200) to call backend (localhost:8000)
    # Without CORS: Browser blocks cross-origin requests
    # With CORS: Frontend can make API calls
    
    # ─────────────────────────────────────────────────────────────────────
    # CUSTOM APPS (Our code)
    # ─────────────────────────────────────────────────────────────────────
    'accounts',
    # User management, authentication, favorites, analytics
    # Files: accounts/models.py, accounts/views.py, accounts/analytics_*.py
    
    'movies',
    # Movie/TV show management, packs, external API integration
    # Files: movies/models.py, movies/views.py
    
    'recommendations',
    # AI-powered recommendation system using ChromaDB + OpenAI
    # Files: recommendations/recommendation_engine.py, recommendations/views.py
    # Movie/TV show management, packs, external API integration
    # Files: movies/models.py, movies/views.py
]

# ═══════════════════════════════════════════════════════════════════════════
# REST FRAMEWORK CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
# Configures Django REST Framework behavior
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # AUTHENTICATION METHOD: JWT tokens
        # 
        # How it works:
        # 1. User logs in → Gets JWT access token
        # 2. Frontend sends token in header: "Authorization: Bearer <token>"
        # 3. This class validates token on every API request
        # 4. If valid: Request allowed, user identified
        # 5. If invalid/missing: 401 Unauthorized error
        #
        # Used by: All /api/* endpoints in backend/urls.py
        # Token validated by: rest_framework_simplejwt library
        # Token generated in: accounts/views.py CustomLoginView
    )
}

# ═══════════════════════════════════════════════════════════════════════════
# MIDDLEWARE - Request/Response Processing Pipeline
# ═══════════════════════════════════════════════════════════════════════════
# Middleware processes EVERY request before it reaches views
# Order matters! Request flows top→bottom, response flows bottom→top
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Adds security headers to responses (X-Frame-Options, etc.)
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Manages sessions (used for admin login)
    # Sessions stored in SQLite db.sqlite3
    # Creates session cookie for logged-in admins
    
    'corsheaders.middleware.CorsMiddleware',
    # ⚠️ MUST BE BEFORE CommonMiddleware
    # Adds CORS headers to allow frontend API calls
    # Without this: Angular can't call Django API (browser blocks)
    
    'django.middleware.common.CommonMiddleware',
    # Basic HTTP handling (redirects, URL normalization)
    
    'django.middleware.csrf.CsrfViewMiddleware',
    # CSRF protection for forms (admin panel forms)
    # Not used for JWT API endpoints (JWT = CSRF protection)
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Associates users with requests (request.user)
    
    'django.contrib.messages.middleware.MessageMiddleware',
    # Enables one-time messages (success/error alerts)
    
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Prevents site from being embedded in <iframe> (security)
]

# ═══════════════════════════════════════════════════════════════════════════
# URL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
ROOT_URLCONF = 'backend.urls'
# Points to backend/urls.py - main URL routing file
# All requests pass through that file first

# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATES CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
# Configures how Django finds and renders HTML templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Template engine (Django's built-in)
        
        'DIRS': [BASE_DIR / 'templates'],
        # Where to find templates
        # Example: templates/accounts/login.html
        # Used by: admin_dashboard, login_page, register_page (accounts/views.py)
        
        'APP_DIRS': True,
        # Also look in each app's templates/ folder
        # Example: accounts/templates/
        
        'OPTIONS': {
            'context_processors': [
                # Functions that add variables to ALL templates
                'django.template.context_processors.request',
                # Adds 'request' variable to templates
                
                'django.contrib.auth.context_processors.auth',
                # Adds 'user' variable to templates
                
                'django.contrib.messages.context_processors.messages',
                # Adds 'messages' variable (for flash messages)
            ],
        },
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# WSGI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════
WSGI_APPLICATION = 'backend.wsgi.application'
# Entry point for WSGI servers (production deployment)
# File: backend/wsgi.py


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
# NOTE: This is SQLite - ONLY used for Django's internal tables
# Main data (users, movies) stored in MongoDB (configured above at line 25)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # SQLite database (single file: db.sqlite3)
        
        'NAME': BASE_DIR / 'db.sqlite3',
        # File location: C:\...\django project backend\db.sqlite3
    }
    # 
    # WHAT'S STORED IN SQLITE:
    #   - Admin sessions (when admin logs in via /admin/login/)
    #   - Django's default User table (not used, we use MongoDB)
    #   - Content types, migrations history
    #
    # WHAT'S STORED IN MONGODB:
    #   - User accounts (accounts.models.User)
    #   - Movies & TV Shows (movies.models.Movie, TVShow)
    #   - Favorites (accounts.models.Favorite)
    #   - Watch Progress (accounts.models.WatchProgress)
    #   - Analytics (UserActivity, UserPreferences, UserSession)
    #   - Packs (movies.models.Pack)
    #
    # WHY TWO DATABASES?
    #   - SQLite: Django framework needs it for sessions/admin
    #   - MongoDB: Better for flexible document storage (movies, users)
}


# ═══════════════════════════════════════════════════════════════════════════
# PASSWORD VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Rules enforced when users register (not strictly enforced in our custom views)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # Password can't be too similar to username/email
        # Example: username="john" → password="john123" = REJECTED
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        # Password must be at least 8 characters
        # Default: 8 characters minimum
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # Blocks common passwords like "password", "12345678"
        # Uses built-in list of 20,000 common passwords
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # Password can't be entirely numeric
        # Example: "12345678" = REJECTED
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# PASSWORD HASHING ALGORITHMS
# ═══════════════════════════════════════════════════════════════════════════
# How passwords are encrypted before saving to database
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
    # MD5 hashing (fast but less secure - only for development)
    # Production should use PBKDF2 or Argon2
    
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    # PBKDF2 with SHA256 (default, recommended)
    # 600,000 iterations = very secure
    # Used by: accounts.models.User.set_password()
]


# ═══════════════════════════════════════════════════════════════════════════
# INTERNATIONALIZATION
# ═══════════════════════════════════════════════════════════════════════════
LANGUAGE_CODE = 'en-us'
# Default language (English - US)

TIME_ZONE = 'UTC'
# Timezone for datetime storage
# All times stored as UTC in database
# Convert to user's local timezone in frontend

USE_I18N = True
# Enable internationalization (translation system)

USE_TZ = True
# Store datetimes as timezone-aware (recommended)


# ═══════════════════════════════════════════════════════════════════════════
# STATIC FILES (CSS, JavaScript, Images)
# ═══════════════════════════════════════════════════════════════════════════
import os

STATIC_URL = '/static/'
# URL prefix for static files
# Example: /static/css/style.css or /static/posters/12345.jpg

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Directory where static files are collected for production

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
# Additional directories where Django looks for static files (posters, etc.)



# ═══════════════════════════════════════════════════════════════════════════
# MEDIA FILES (User Uploads - Posters, Images)
# ═══════════════════════════════════════════════════════════════════════════
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'static')

# ═══════════════════════════════════════════════════════════════════════════
# CORS (Cross-Origin Resource Sharing) CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
# Allows Angular frontend (localhost:4200) to call Django API (localhost:8000)

CORS_ALLOW_ALL_ORIGINS = True
# ⚠️ WARNING: Allows requests from ANY domain
# Development: True (convenient)
# Production: Should specify exact origins:
#   CORS_ALLOWED_ORIGINS = [
#       'https://moviehub.com',
#       'https://www.moviehub.com',
#   ]
#
# WHY CORS IS NEEDED:
#   - Browser security blocks cross-origin requests by default
#   - Frontend: http://localhost:4200
#   - Backend:  http://localhost:8000
#   - Different origins → Browser blocks
#   - CORS headers tell browser: "It's okay, allow it"

CORS_ALLOW_CREDENTIALS = True
# Allows cookies/auth headers in cross-origin requests
# Needed for: JWT tokens in Authorization header
# Without this: Frontend can't send "Authorization: Bearer <token>"

# ═══════════════════════════════════════════════════════════════════════════
# ALLOWED HTTP METHODS
# ═══════════════════════════════════════════════════════════════════════════
# Which HTTP methods frontend can use
CORS_ALLOW_METHODS = [
    'DELETE',   # Used by: deleteMovie, deleteUser, deletePack
    'GET',      # Used by: getMovies, getFavorites, getAnalytics
    'OPTIONS',  # Preflight requests (browser sends automatically)
    'PATCH',    # Partial updates (not used much in this project)
    'POST',     # Used by: login, register, addMovie, toggleFavorite
    'PUT',      # Used by: editMovie, updatePack
]

# ═══════════════════════════════════════════════════════════════════════════
# ALLOWED HTTP HEADERS
# ═══════════════════════════════════════════════════════════════════════════
# Which headers frontend can send in requests
CORS_ALLOW_HEADERS = [
    'accept',           # Content negotiation
    'accept-encoding',  # Compression (gzip)
    'authorization',    # ⭐ CRITICAL: JWT tokens sent here
                       # Example: "Authorization: Bearer eyJhbGc..."
    'content-type',     # JSON data type
    'dnt',             # Do Not Track
    'origin',          # Request origin
    'user-agent',      # Browser info
    'x-csrftoken',     # CSRF protection (for non-JWT endpoints)
    'x-requested-with', # AJAX identification
]

# ═══════════════════════════════════════════════════════════════════════════
# EMAIL CONFIGURATION (For Password Reset)
# ═══════════════════════════════════════════════════════════════════════════
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Development: Print emails to console (no actual sending)
# This allows testing password reset without SMTP server
# The verification code will appear in the Django console

EMAIL_HOST_USER = 'noreply@moviehub.com'
# Sender email address (for console backend, can be any value)

# Production configuration (uncomment and configure for real emails):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.getenv('EMAIL_USER')  # Your email
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')  # App password

# ═══════════════════════════════════════════════════════════════════════════
# JWT (JSON Web Token) AUTHENTICATION SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
# Configures how JWT tokens are generated and validated
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    # Access token expires after 1 hour
    # User must refresh or re-login after 1 hour
    # Short lifetime = more secure (if token stolen, expires quickly)
    
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # Refresh token expires after 7 days
    # Used to get new access token without re-login
    # After 7 days, user must login again
    
    'ROTATE_REFRESH_TOKENS': False,
    # If True: New refresh token issued when refreshing access token
    # If False: Same refresh token reused (our setting)
    
    'BLACKLIST_AFTER_ROTATION': False,
    # Blacklist old refresh tokens after rotation
    # Not used since ROTATE_REFRESH_TOKENS=False
    
    'ALGORITHM': 'HS256',
    # Encryption algorithm: HMAC with SHA-256
    # Industry standard for JWT signing
    
    'SIGNING_KEY': SECRET_KEY,
    # Secret key used to sign tokens
    # Uses Django's SECRET_KEY (line 69)
    # Must keep secret! If exposed, attackers can forge tokens
    
    'VERIFYING_KEY': None,
    # Public key for asymmetric algorithms (RS256)
    # None = symmetric algorithm (HS256) used
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    # Token sent as: "Authorization: Bearer <token>"
    # 'Bearer' is the industry standard prefix
    #
    # Request flow:
    # 1. Frontend: sessionStorage.setItem('access_token', 'eyJ...')
    # 2. Interceptor: req.headers.Authorization = 'Bearer eyJ...'
    # 3. Backend: Extracts token after 'Bearer '
    # 4. Validates token using SIGNING_KEY
    
    'USER_ID_FIELD': 'id',
    # Which field identifies user in token payload
    # Token contains: {"user_id": "507f1f77bcf86cd799439011"}
    
    'USER_ID_CLAIM': 'user_id',
    # Claim name in token for user ID
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    # Token class used for authentication
    # AccessToken = standard JWT access token
    
    'TOKEN_TYPE_CLAIM': 'token_type',
    # Token contains: {"token_type": "access"}
    # Distinguishes access tokens from refresh tokens
}

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 CONFIGURATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATABASE SETUP:
    MongoDB (Main Database):
        - Connection: Line 42-58
        - Database: "MovieApp"
        - Collections: users, movies, tv_shows, favorites, watch_progress, etc.
        - Used for: All app data
    
    SQLite (Django Internal):
        - File: db.sqlite3
        - Used for: Admin sessions, migrations history
        - Not used for: App data

AUTHENTICATION:
    JWT Tokens (API endpoints):
        - Access token: 1 hour lifetime
        - Refresh token: 7 days lifetime
        - Algorithm: HS256
        - Header: "Authorization: Bearer <token>"
    
    Session Auth (Admin panel):
        - Stored in SQLite
        - Cookie-based
        - Used for: /admin/* routes

CORS (Frontend Communication):
    - Allow all origins: True (development only!)
    - Allow credentials: True (for JWT headers)
    - Allowed methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
    - Critical header: 'authorization' (for JWT tokens)

SECURITY:
    - SECRET_KEY: Used for signing, should be in .env
    - DEBUG: True (development), must be False in production
    - Password hashing: PBKDF2 with SHA256
    - HTTPS: Not configured (add in production)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


