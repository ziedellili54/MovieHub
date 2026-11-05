"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 ACCOUNTS MODELS - User Data Structures (MongoDB Collections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Defines the structure of user-related data stored in MongoDB.
    These are like blueprints that tell MongoDB what fields each document should have.

MODELS IN THIS FILE:
    1. User - User accounts with secure password hashing
    2. Favorite - Tracks which movies users have favorited
    3. WatchProgress - Remembers where user stopped watching (like Netflix)

MONGODB COLLECTIONS CREATED:
    - 'users' collection → Stores User documents
    - 'favorites' collection → Stores Favorite documents
    - 'watch_progress' collection → Stores WatchProgress documents

RELATED FILES:
    - accounts/views.py → Uses these models to read/write data
    - backend/settings.py → MongoDB connection configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from mongoengine import Document, StringField, IntField, ListField
from django.contrib.auth.hashers import make_password, check_password


# ═══════════════════════════════════════════════════════════════════════════
# MODEL 1: User (User Accounts with Authentication)
# ═══════════════════════════════════════════════════════════════════════════
# MongoDB Collection: 'users'
# Purpose: Store user account information with secure password hashing
# Used By: CustomLoginView, CustomRegisterView in accounts/views.py
# ═══════════════════════════════════════════════════════════════════════════
class User(Document):
    # ─────────────────────────────────────────────────────────────────────
    # USER FIELDS - What data each user document contains
    # ─────────────────────────────────────────────────────────────────────
    
    username = StringField(required=True, unique=True, max_length=150)
    # Username for login (e.g., "john", "admin")
    # required=True → Can't be empty
    # unique=True → No two users can have same username
    # max_length=150 → Maximum 150 characters
    
    email = StringField(unique=True)
    # User's email address (e.g., "john@email.com")
    # unique=True → Each email can only be registered once
    # Also used for login (alternative to username)
    
    user_id = StringField(unique=True)
    # Custom user ID generated during registration
    # Format: 8 random characters (e.g., "abc12345")
    # Used for identifying users in other systems
    
    password = StringField(required=True)
    # 🔒 SECURITY: Never stores plain text password!
    # Stores hashed (encrypted) password
    # Example stored value: "pbkdf2_sha256$600000$..."
    # Even if database is hacked, real passwords stay safe
    
    role = StringField(default='user')
    # User role: 'user' or 'admin'
    # Default is 'user' for regular users
    
    is_admin = StringField(default='false')
    # Whether user has admin privileges (legacy field)
    # Stored as string 'true' or 'false' for MongoDB compatibility
    
    created_at = StringField()
    # When user account was created
    # Format: ISO datetime string
    
    ip_address = StringField()
    # IP address from registration (for security tracking)
    
    favorites = ListField(StringField(), default=list)
    # List of favorite movie IDs (for backward compatibility with existing data)

    meta = {
        'collection': 'users'
        # MongoDB collection name where User documents are stored
    }

    # ─────────────────────────────────────────────────────────────────────
    # METHOD 1: set_password() - Securely hash password before saving
    # ─────────────────────────────────────────────────────────────────────
    def set_password(self, raw_password):
        """
        Converts plain text password to secure hash before saving to database
        
        SECURITY:
            - Uses Django's make_password() (industry standard)
            - One-way encryption (can't decrypt back to original)
            - Even database admin can't see real passwords
        
        Example Usage:
            user = User(username="john", email="john@email.com")
            user.set_password("mypassword123")  # Hashes the password
            user.save()  # Saves hashed version to MongoDB
        
        What Gets Stored:
            Input: "mypassword123"
            Stored: "pbkdf2_sha256$600000$randomsalt$longhashvalue"
        
        Called By:
            - CustomRegisterView.post() when creating new user
            - register_page() when user signs up via HTML form
        """
        self.password = make_password(raw_password)

    # ─────────────────────────────────────────────────────────────────────
    # METHOD 2: check_password() - Verify password during login
    # ─────────────────────────────────────────────────────────────────────
    def check_password(self, raw_password):
        """
        Compares typed password with stored hash to verify identity
        
        How It Works:
            1. User types password (e.g., "mypassword123")
            2. This method hashes it the same way
            3. Compares with stored hash
            4. Returns True if match, False if wrong
        
        Example Usage:
            user = User.objects(username="john").first()
            if user.check_password("mypassword123"):
                print("✓ Password correct! User can login")
            else:
                print("✗ Wrong password! Access denied")
        
        Returns:
            bool: True if password matches, False if wrong
        
        Called By:
            - CustomLoginView.post() during JWT login
            - login_page() during HTML form login
            - admin_login_page() during admin login
        
        Security Note:
            This method is secure because:
            - Doesn't return the actual password
            - Uses constant-time comparison (prevents timing attacks)
            - Automatically handles different hashing algorithms
        """
        return check_password(raw_password, self.password)

    def __str__(self):
        # String representation (for debugging/admin panel)
        # Returns username if available, otherwise email
        return self.username or self.email or "Unnamed User"


# ═══════════════════════════════════════════════════════════════════════════
# MODEL 2: Favorite (User's Favorite Movies)
# ═══════════════════════════════════════════════════════════════════════════
# MongoDB Collection: 'favorites'
# Purpose: Track which movies/shows each user has favorited
# Used By: FavoritesView in accounts/views.py
# ═══════════════════════════════════════════════════════════════════════════
class Favorite(Document):
    # ─────────────────────────────────────────────────────────────────────
    # FAVORITE FIELDS
    # ─────────────────────────────────────────────────────────────────────
    
    username = StringField(required=True)
    # Which user favorited this (e.g., "john")
    # Links to User.username
    
    movie_id = StringField(required=True)
    # Which movie was favorited (e.g., "abc123")
    # Links to Movie.id or TVShow.id in movies collection

    meta = {
        'collection': 'favorites',
        'indexes': [
            {'fields': ['username', 'movie_id'], 'unique': True}
            # COMPOSITE UNIQUE INDEX:
            # Prevents duplicate favorites
            # User can't favorite same movie twice
            # But different users can favorite same movie
            # 
            # Example Valid Documents:
            #   {username: "john", movie_id: "abc123"} ✓
            #   {username: "jane", movie_id: "abc123"} ✓ (different user)
            # 
            # Example Invalid (Duplicate):
            #   {username: "john", movie_id: "abc123"} ✗ (already exists)
        ]
    }
    
    # Example MongoDB Document:
    # {
    #     "_id": ObjectId("..."),
    #     "username": "john",
    #     "movie_id": "abc123"
    # }
    
    # HOW FAVORITES WORK:
    # 1. User clicks heart icon on movie → POST /api/favorites/john/
    # 2. FavoritesView checks if Favorite exists
    # 3. If exists: Delete it (unfavorite)
    # 4. If not exists: Create it (favorite)
    # 5. Response includes is_favorite: true/false


# ═══════════════════════════════════════════════════════════════════════════
# MODEL 3: WatchProgress (Continue Watching Feature)
# ═══════════════════════════════════════════════════════════════════════════
# MongoDB Collection: 'watch_progress'
# Purpose: Remember where user stopped watching (like Netflix's "Continue Watching")
# Used By: get_watch_progress(), update_watch_progress() in accounts/views.py
# ═══════════════════════════════════════════════════════════════════════════
class WatchProgress(Document):
    """
    Tracks watch progress for each movie/show per user
    
    Use Cases:
        - User watches 50% of movie, closes app
        - Comes back later → sees "Continue Watching" at 50%
        - Video player loads from 50% position
    
    Example Flow:
        1. User starts watching "Inception"
        2. Video player sends progress updates every 30 seconds
        3. POST /api/watch-progress/update/ {username: "john", movie_id: "abc123", progress: 25, watching_percentage: 45}
        4. Document created/updated in MongoDB
        5. When user returns, GET /api/watch-progress/?username=john
        6. Response includes progress: 25% for "Inception", watching: 45%
    """
    
    # ─────────────────────────────────────────────────────────────────────
    # WATCH PROGRESS FIELDS
    # ─────────────────────────────────────────────────────────────────────
    
    username = StringField(required=True)
    # Which user is watching (e.g., "john")
    
    movie_id = StringField(required=True)
    # Which movie/show (e.g., "abc123")
    
    progress_percentage = IntField(default=0, min_value=0, max_value=100)
    # How much watched (0-100%)
    # Examples:
    #   0 = Just started
    #   50 = Watched half
    #   100 = Finished
    # 
    # Validation:
    #   min_value=0 → Can't be negative
    #   max_value=100 → Can't exceed 100%
    #   default=0 → New documents start at 0%
    
    watching_percentage = IntField(default=0, min_value=0, max_value=100)
    # User-adjustable input percentage (0-100%)
    # Can be changed by user in UI
    # Default: 0% until user changes it
    # Stored in MongoDB and counts for AI activity tracking
    # min_value=0 → Can't be negative
    # max_value=100 → Can't exceed 100%
    
    last_watched_at = StringField()
    # Timestamp when last updated
    # Format: ISO 8601 (e.g., "2024-01-15T10:30:00")
    # Used to sort by "Recently Watched"

    meta = {
        'collection': 'watch_progress',
        'indexes': [
            {'fields': ['username', 'movie_id'], 'unique': True}
            # COMPOSITE UNIQUE INDEX:
            # One progress record per user per movie
            # If user watches same movie again, updates existing record
        ]
    }

    def __str__(self):
        # Readable representation for debugging
        # Example: "john - abc123: 75%"
        return f"{self.username} - {self.movie_id}: {self.progress_percentage}%"
    
    # Example MongoDB Document:
    # {
    #     "_id": ObjectId("..."),
    #     "username": "john",
    #     "movie_id": "abc123",
    #     "progress_percentage": 75,
    #     "watching_percentage": 45,
    #     "last_watched_at": "2024-01-15T10:30:00"
    # }


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MODELS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODEL               COLLECTION          PURPOSE                 KEY FIELDS
─────────────────────────────────────────────────────────────────────────────
User                'users'             User accounts           username, email, password
Favorite            'favorites'         User favorites          username, movie_id
WatchProgress       'watch_progress'    Watch tracking          username, movie_id, progress_percentage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 SECURITY NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASSWORD HASHING:
    ✓ Uses Django's make_password() - industry standard
    ✓ PBKDF2 algorithm with SHA256
    ✓ 600,000 iterations (slow = more secure)
    ✓ Automatic salt generation (unique per password)
    ✓ One-way encryption (can't decrypt)

WHY THIS MATTERS:
    Even if someone hacks the database, they can't use the passwords because:
    1. They're all hashed (not plain text)
    2. Each password has unique salt (can't use rainbow tables)
    3. Hashing is slow (can't brute force quickly)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""