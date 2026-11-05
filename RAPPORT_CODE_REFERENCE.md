# CODE REFERENCE FOR RAPPORT — MovieHub Platform
> Upload this file to any AI model and ask it to explain any section,
> suggest where to place it in your rapport, or expand on any concept.
> Each section includes: what the code does, where it lives, and where it fits in the rapport.

---

## HOW TO USE THIS FILE

Ask the AI things like:
- "Explain section 3 in simple terms for a rapport"
- "Where in my rapport should I put section 5?"
- "Write a paragraph describing the authentication system for my rapport"
- "What rapport chapter does section 7 belong to?"

---

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — PROJECT ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════
# RAPPORT LOCATION: Chapter "Présentation du projet" or "Architecture technique"
# POINT: Shows the full-stack architecture and technology choices

```
FRONTEND                    BACKEND                     DATABASE
─────────                   ───────                     ────────
Angular 17                  Django 5.2 (Python)         MongoDB Atlas
TypeScript                  Django REST Framework        Collections:
Angular Material            JWT Authentication           - movies
Vite build tool             MongoEngine ORM              - tv_shows
                            CORS headers                 - users
Port: 4200                                               - favorites
                            Port: 8000                   - user_activities
                                                         - user_preferences
                                                         - movie_watch_history
                                                         - recommendation_feedback
                                                         - packs
                                          
                                          SQLITE (internal)
                                          - Django sessions (admin only)

AI LAYER:
  TensorFlow Hub — Universal Sentence Encoder v4 (512-dim vectors)
  Custom SimpleVectorStore (numpy + pickle, no external vector DB)
  
EXTERNAL APIs:
  - RapidAPI Netflix DB (fetch movies by year)
  - OMDb API (search movies by title, get details + poster)
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 2 — DATABASE MODELS (MongoDB Collections)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/movies/models.py
# RAPPORT LOCATION: Chapter "Conception" → "Modèle de données"
# POINT: Defines the data structure for movies, TV shows, and packs stored in MongoDB

```python
# FILE: movies/models.py
from mongoengine import Document, StringField, IntField, ListField, FloatField

class Movie(Document):
    """Stores individual movie data in MongoDB 'movies' collection"""
    show_id      = StringField()   # External IMDb ID (e.g. "tt1375666")
    title        = StringField()   # Movie title
    type         = StringField()   # "Movie"
    director     = StringField()   # Director name(s)
    cast         = StringField()   # Comma-separated actor names
    country      = StringField()   # Country of origin
    release_year = IntField()      # Year (enables range filtering & sorting)
    rating       = StringField()   # Age rating: "PG-13", "R", "TV-MA"
    duration     = StringField()   # "148 min"
    listed_in    = StringField()   # Genres: "Action, Sci-Fi, Thriller"
    primary_category = StringField() # Main genre (used by AI for filtering)
    description  = StringField()   # Plot summary
    poster       = StringField()   # Image URL
    imdb_rating  = FloatField(default=0.0)  # 0.0–10.0 (for trending sort)
    imdb_votes   = IntField(default=0)      # Popularity metric

    meta = {'collection': 'movies'}


class TVShow(Document):
    """Same structure as Movie, stored in separate 'tv_shows' collection"""
    # Identical fields as Movie, with default type='TV Show'
    # Both collections are queried together when displaying to users
    # Separation allows efficient filtering (movies-only or shows-only)
    meta = {'collection': 'tv_shows'}


class Pack(Document):
    """Themed movie collections (like Netflix categories)"""
    name         = StringField(required=True)  # "Action Heroes 2024"
    genres       = ListField(StringField())    # Filter: ["Action", "Sci-Fi"]
    years        = ListField(IntField())       # Filter: [2023, 2024]
    movie_ids    = ListField(StringField())    # Handpicked specific movies
    level        = IntField(default=1)         # Display order (1 = top)
    cover_image  = StringField()               # Banner image URL
    cover_height = IntField(default=250)       # Height in pixels
    
    meta = {'collection': 'packs', 'ordering': ['level']}
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 3 — USER MODELS & AUTHENTICATION
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/accounts/models.py
# RAPPORT LOCATION: Chapter "Conception" → "Gestion des utilisateurs"
# POINT: User accounts with secure password hashing and favorites/watch progress tracking

```python
# FILE: accounts/models.py
from mongoengine import Document, StringField, IntField
from django.contrib.auth.hashers import make_password, check_password

class User(Document):
    """User accounts stored in MongoDB 'users' collection"""
    username = StringField(required=True, unique=True, max_length=150)
    email    = StringField(unique=True)
    user_id  = StringField(unique=True)  # 8-char generated ID
    password = StringField(required=True) # NEVER plain text — always hashed
    role     = StringField(default='user') # 'user' or 'admin'
    
    meta = {'collection': 'users'}

    def set_password(self, raw_password):
        """Hash password using PBKDF2+SHA256 before saving to DB"""
        self.password = make_password(raw_password)
        # Result: "pbkdf2_sha256$600000$randomsalt$longhashvalue"
        # Even if DB is hacked, real passwords stay safe

    def check_password(self, raw_password):
        """Verify login: hash the typed password, compare with stored hash"""
        return check_password(raw_password, self.password)
        # Returns True = access granted, False = wrong password


class Favorite(Document):
    """Tracks which movies each user favorited"""
    username = StringField(required=True)
    movie_id = StringField(required=True)
    
    meta = {
        'collection': 'favorites',
        'indexes': [
            {'fields': ['username', 'movie_id'], 'unique': True}
            # Prevents duplicate favorites (one per user per movie)
        ]
    }


class WatchProgress(Document):
    """Remember where user stopped watching (Continue Watching feature)"""
    username            = StringField(required=True)
    movie_id            = StringField(required=True)
    progress_percentage = IntField(default=0, min_value=0, max_value=100)
    watching_percentage = IntField(default=0, min_value=0, max_value=100)
    last_watched_at     = StringField()  # ISO timestamp
    
    meta = {
        'collection': 'watch_progress',
        'indexes': [{'fields': ['username', 'movie_id'], 'unique': True}]
    }
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 4 — JWT AUTHENTICATION (Login API)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/accounts/views.py
# RAPPORT LOCATION: Chapter "Sécurité" or "API REST" → "Authentification"
# POINT: How the Angular frontend logs in and receives JWT tokens for secured API calls

```python
# FILE: accounts/views.py
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class CustomLoginView(APIView):
    """
    POST /api/login/
    Body: { "username": "john", "password": "mypass123" }
    Returns: { "access": "<JWT>", "refresh": "<JWT>", "username": "john", "role": "user" }
    
    Flow:
      1. User sends username + password
      2. Server finds user in MongoDB
      3. Verifies password against stored hash
      4. Generates JWT access token (1 hour) + refresh token (7 days)
      5. Frontend stores tokens in sessionStorage
      6. Every API call includes: "Authorization: Bearer <access_token>"
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # Supports login by username OR email (case-insensitive)
        if "@" in username:
            user = User.objects(email__iexact=username).first()
        else:
            user = User.objects(username__iexact=username).first()

        if user and user.check_password(password):
            # Generate JWT tokens
            refresh = RefreshToken()
            refresh["username"] = user.username
            refresh["user_id"] = str(user.id)

            return Response({
                "access":   str(refresh.access_token),  # Short-lived (1hr)
                "refresh":  str(refresh),                # Long-lived (7 days)
                "username": user.username,
                "role": "admin" if user.username.lower() == "admin" else "user"
            }, status=200)
        
        return Response({"error": "Invalid credentials"}, status=401)


class CustomRegisterView(APIView):
    """
    POST /api/register/
    Body: { "username", "email", "password", "confirm_password" }
    Creates new user in MongoDB with hashed password
    """
    def post(self, request):
        # Validate all fields
        # Check duplicate username/email
        user = User(username=username, email=email, user_id=user_id)
        user.set_password(password)  # Hash before saving
        user.save()                   # Save to MongoDB
        return Response({"message": "Registration successful"}, status=201)
```

**JWT Settings (backend/settings.py):**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=1),   # Expires in 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Refresh lasts 7 days
    'ALGORITHM': 'HS256',                            # HMAC SHA-256 signing
    'AUTH_HEADER_TYPES': ('Bearer',),               # "Authorization: Bearer <token>"
}
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 5 — ANALYTICS MODELS (User Behavior Tracking)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/accounts/analytics_models.py
# RAPPORT LOCATION: Chapter "Fonctionnalités" → "Analytique" or "Système IA"
# POINT: How user behavior is tracked to feed the AI recommendation engine

```python
# FILE: accounts/analytics_models.py

class UserActivity(Document):
    """
    Logs EVERY user action — the raw data stream for analytics and AI.
    MongoDB collection: 'user_activities'
    
    Every search, click, watch, like, dislike creates one document here.
    """
    username             = StringField(required=True)
    activity_type        = StringField(required=True)
    # Activity types: "search", "movie_watch", "movie_click",
    #                 "like", "dislike", "add_watchlist", "movie_finish"
    
    movie_id             = StringField()   # Which movie (if applicable)
    movie_title          = StringField()   # Denormalized for fast queries
    genres               = ListField(StringField())  # ["Action", "Sci-Fi"]
    
    watch_duration_seconds = IntField()   # How long watched this session
    watch_percentage       = FloatField() # Progress 0–100%
    search_query           = StringField() # What user searched for
    
    device_type = StringField()  # "desktop", "mobile", "tablet"
    browser     = StringField()  # "Chrome", "Firefox"
    timestamp   = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'user_activities'}


class UserPreferences(Document):
    """
    ONE document per user — aggregated summary of their behavior.
    MongoDB collection: 'user_preferences'
    
    Updated automatically when UserActivity records are created.
    Used by AI for fast genre preference lookup.
    """
    username                    = StringField(required=True, unique=True)
    favorite_genres             = ListField(StringField())  # ["Action", "Sci-Fi"]
    total_movies_watched        = IntField(default=0)
    total_searches              = IntField(default=0)
    average_watch_percentage    = FloatField()  # 85.5 = watches 85% on average
    recommendation_score        = DictField()   # {"Action": 95, "Drama": 75}
    # ↑ AI learning scores — persist across sessions
    
    meta = {'collection': 'user_preferences'}


class MovieWatchHistory(Document):
    """
    ONE record per user+movie — cumulative watch time tracking.
    MongoDB collection: 'movie_watch_history'
    
    AI uses this to find which movies user spent MOST time on.
    Unlike UserActivity (many records), this is ONE aggregated record.
    """
    username                  = StringField(required=True)
    movie_id                  = StringField(required=True)
    movie_title               = StringField()
    total_watch_time_seconds  = IntField(default=0)  # Cumulative all sessions
    watch_count               = IntField(default=0)  # Times watched
    watch_percentage          = FloatField(default=0.0)  # Latest position
    completed                 = BooleanField(default=False)  # Watched 90%+
    genres                    = ListField(StringField())
    last_watched              = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'movie_watch_history',
        'indexes': [
            {'fields': ['username', 'movie_id'], 'unique': True},
            '-total_watch_time_seconds'  # Fast sort by most-watched
        ]
    }


class RecommendationFeedback(Document):
    """
    Tracks AI recommendation performance — reinforcement learning.
    MongoDB collection: 'recommendation_feedback'
    
    When user clicks a recommendation, AI scores its own performance:
    - Position 1–5:  +10 pts (excellent — user loved top picks)
    - Position 6–10: +5 pts  (good)
    - Position 11–20: 0 pts  (neutral)
    - Position 21–50: -1 per position (bad — skipped better options)
    - Position 51+:   -2 per position (very bad — AI failed)
    """
    username                = StringField(required=True)
    recommended_movie_id    = StringField(required=True)
    recommendation_position = IntField(required=True)  # 1 = best, 100 = worst
    similarity_score        = FloatField()             # AI confidence 0–100%
    feedback_score          = IntField(default=0)      # Points gained/lost
    feedback_category       = StringField()            # "excellent"/"good"/"bad"
    
    meta = {'collection': 'recommendation_feedback'}
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 6 — AI RECOMMENDATION ENGINE (Core Algorithm)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/recommendations/recommendation_engine.py
# RAPPORT LOCATION: Chapter "Intelligence Artificielle" or "Système de recommandation"
# POINT: The heart of the AI — how movies are embedded and recommendations generated

```python
# FILE: recommendations/recommendation_engine.py
import tensorflow_hub as hub
import numpy as np
from .vector_store import SimpleVectorDB

class RecommendationEngine:
    """
    AI recommendation system using:
    - TensorFlow Hub Universal Sentence Encoder v4 (free, 512-dim vectors)
    - Custom vector store (numpy cosine similarity, no external DB needed)
    - Multi-genre blending to prevent single-genre collapse
    """

    def __init__(self):
        # Load Google's Universal Sentence Encoder from TensorFlow Hub
        # Converts text descriptions into 512-dimensional vectors
        self.embed_model = hub.load(
            "https://tfhub.dev/google/universal-sentence-encoder/4"
        )
        # Initialize local vector database (stores movie embeddings on disk)
        self.vector_db = SimpleVectorDB(path="./vector_db")
        self.movies_collection = self.vector_db.get_or_create_collection(
            name="movies",
            metadata={"model": "tensorflow-hub-use-v4"}
        )

    # ── STEP 1: Convert movie to searchable text ──────────────────────────
    def create_movie_text(self, movie) -> str:
        """
        Build a rich text description for embedding.
        Primary genre is repeated 3× to give AI a stronger genre signal.
        
        Example output:
        "Primary Genre: Action. Category: Action. Main Genre: Action.
         Secondary Genres: Thriller. Type: Movie. Year: 2024.
         Plot: A hero must save the world..."
        """
        parts = []
        if movie.primary_category:
            # Repeat 3x = stronger genre signal in embedding space
            parts.append(
                f"Primary Genre: {movie.primary_category}. "
                f"Category: {movie.primary_category}. "
                f"Main Genre: {movie.primary_category}"
            )
        if movie.listed_in:
            genres = movie.listed_in.split(',')
            secondary = genres[1:3]  # Up to 2 secondary genres
            if secondary:
                parts.append(f"Secondary Genres: {', '.join(secondary)}")
        if movie.type:
            parts.append(f"Type: {movie.type}")
        if movie.release_year:
            parts.append(f"Year: {movie.release_year}")
        if movie.description:
            parts.append(f"Plot: {movie.description[:300]}")
        return ". ".join(parts)

    # ── STEP 2: Generate vector embedding ────────────────────────────────
    def generate_embedding(self, text: str) -> List[float]:
        """
        Convert text → 512-dimensional vector using TensorFlow Hub.
        Similar texts produce similar vectors (close in vector space).
        """
        embedding = self.embed_model([text])
        return embedding.numpy()[0].tolist()  # Returns list of 512 floats

    # ── STEP 3: Index all movies into vector database ─────────────────────
    def index_movie(self, movie) -> bool:
        """
        Embed a movie and store in vector database.
        Called once for all movies (and when new movies are added).
        """
        movie_text = self.create_movie_text(movie)
        embedding = self.generate_embedding(movie_text)
        
        self.movies_collection.upsert(
            ids=[str(movie.id)],
            embeddings=[embedding],      # 512-dim vector
            metadatas=[{
                "title": movie.title,
                "type": movie.type,
                "genres": movie.listed_in,
                "release_year": str(movie.release_year),
            }],
            documents=[movie_text]
        )
        return True

    # ── STEP 4: Compute user genre weights ───────────────────────────────
    def _compute_genre_weights(self, username: str) -> Dict[str, float]:
        """
        Calculate how much each genre matters to this user.
        Combines 4 data sources with different priorities:
        
        Source 1 — UserPreferences.recommendation_score (persisted AI learning)
        Source 2 — Favorites: weight 300 (primary) / 100 (secondary)
        Source 3 — UserActivity: real engagement only (watch/play/complete)
                   Recency decay: newest = 100%, oldest = 15% (floor)
                   Window: last 60 activities
        Source 4 — MovieWatchHistory: scaled by completion %
                   Watched 100% → full weight; watched 20% → 20% weight
        
        Returns: {"Action": 850.0, "Sci-Fi": 420.0, "Drama": 180.0, ...}
        """
        genre_weights = {}
        
        # Source 1: Stored AI learning scores
        prefs = UserPreferences.objects.get(username=username)
        for genre, score in (prefs.recommendation_score or {}).items():
            genre_weights[genre] = genre_weights.get(genre, 0) + score
        
        # Source 2: Favorites (highest stable weight)
        for fav in Favorite.objects(username=username)[:20]:
            movie = self._get_movie_or_show(fav.movie_id)
            if movie and movie.listed_in:
                self._add_genre_weights(genre_weights, movie.listed_in,
                                        primary=300, secondary=100)
        
        # Source 3: Activity — real engagement, softer decay
        activities = UserActivity.objects(username=username).order_by('-timestamp')[:60]
        engagement = [a for a in activities
                      if a.action in ('watch', 'play', 'complete')
                      or a.watch_time_minutes > 0]
        
        for idx, activity in enumerate(engagement):
            decay = max(0.15, 1 - (idx / max(len(engagement), 1)) * 0.85)
            base_weight = 40 * decay  # Newest: 40pts, oldest: ~6pts
            movie = self._get_movie_or_show(activity.movie_id)
            if movie and movie.listed_in:
                self._add_genre_weights(genre_weights, movie.listed_in,
                                        primary=base_weight * 3, secondary=base_weight)
        
        # Source 4: Watch history — scaled by completion
        for watch in MovieWatchHistory.objects(username=username)[:40]:
            completion = max(0.2, min(1.0, watch.watch_percentage / 100))
            movie = self._get_movie_or_show(watch.movie_id)
            if movie and movie.listed_in:
                self._add_genre_weights(genre_weights, movie.listed_in,
                                        primary=60 * completion,
                                        secondary=20 * completion)
        return genre_weights

    # ── STEP 5: Find important genres ────────────────────────────────────
    def get_top_user_genres(self, username: str, min_share: float = 0.08) -> List[Dict]:
        """
        Return genres that represent ≥8% of user's total weight.
        Always returns at least TOP 2 genres to ensure variety.
        
        Example: {"Action": 850, "Sci-Fi": 420, "Drama": 180}
          Total = 1450
          Action share = 58.6%  → included
          Sci-Fi share = 29.0%  → included
          Drama share  = 12.4%  → included
        
        Returns: [
          {"genre": "Action", "weight": 850, "share": 0.586},
          {"genre": "Sci-Fi", "weight": 420, "share": 0.290},
          {"genre": "Drama",  "weight": 180, "share": 0.124}
        ]
        """
        genre_weights = self._compute_genre_weights(username)
        total = sum(genre_weights.values())
        
        important = [
            {"genre": g, "weight": w, "share": w / total}
            for g, w in genre_weights.items()
            if (w / total) >= min_share
        ]
        important.sort(key=lambda x: x["weight"], reverse=True)
        
        # Always ensure at least 2 genres (prevent mono-genre recommendations)
        if len(important) < 2 and len(genre_weights) >= 2:
            all_genres = sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)
            important = [{"genre": g, "weight": w, "share": w/total}
                         for g, w in all_genres[:2]]
        
        return important[:4]  # Max 4 genres

    # ── STEP 6: Generate recommendations ─────────────────────────────────
    def get_recommendations(self, username: str, n_recommendations: int = 20,
                            filters=None) -> List[Dict]:
        """
        Main recommendation function.
        
        Decision tree:
        1. < 3 watched movies → return trending/popular (cold start)
        2. ≥ 2 important genres → MULTI-GENRE BLENDING (main algorithm)
        3. Only 1 dominant genre → single profile search (fallback)
        
        The multi-genre blending fix prevents this common bug:
        "User watches Action movies for weeks, then watches ONE Sci-Fi film →
         ALL recommendations flip to Sci-Fi, Action disappears"
        
        Fix: Query vector DB separately per genre, then interleave results:
          Action quota:  60% (12 movies) — primary genre
          Sci-Fi quota:  30% (6 movies)  — secondary genre
          Drama quota:   10% (2 movies)  — tertiary genre
          Final list: Action, Sci-Fi, Action, Drama, Action, Sci-Fi, ...
        """
        # Cold start: new user
        watch_history = MovieWatchHistory.objects(username=username)
        if len(list(watch_history)) < 3:
            return self.get_popular_movies(n_recommendations, filters)
        
        # Build exclusion set (already watched, favorites, dislikes)
        watched_ids = {str(w.movie_id) for w in watch_history}
        watched_ids.update({str(f.movie_id) for f in Favorite.objects(username=username)})
        watched_ids.update({str(d.movie_id) for d in MovieDislike.objects(username=username)})
        
        # Multi-genre blending
        top_genres = self.get_top_user_genres(username, min_share=0.15)
        if len(top_genres) >= 2:
            return self._get_blended_recommendations(
                top_genres, watched_ids, n_recommendations, filters
            )
        
        # Fallback: single profile
        return self._get_single_profile_recommendations(
            username, watched_ids, n_recommendations, filters
        )

    def _get_blended_recommendations(self, top_genres, watched_ids,
                                      n_recommendations, filters) -> List[Dict]:
        """
        Query vector DB SEPARATELY per genre, then interleave results.
        
        For each genre:
          1. Build genre embedding: "Primary Genre: Action. Category: Action."
          2. Query vector DB for most similar movies
          3. Fill quota (primary=60%, secondary=30%, others=10%)
        
        Interleaving pattern (2 genres, 10 total):
          Genre A: [A1, A2, A3, A4, A5, A6]  ← 60%
          Genre B: [B1, B2, B3]               ← 30%
          Result:  [A1, B1, A2, B2, A3, B3, A4, A5, A6]
        """
        buckets = []
        
        for idx, genre_info in enumerate(top_genres):
            genre = genre_info["genre"]
            
            # Assign quota by position
            if idx == 0:   quota = max(1, round(n_recommendations * 0.60))
            elif idx == 1: quota = max(1, round(n_recommendations * 0.30))
            else:          quota = max(1, round(n_recommendations * 0.10))
            
            # Build genre query embedding
            genre_text = f"Primary Genre: {genre}. Category: {genre}. Main Genre: {genre}"
            genre_embedding = self.generate_embedding(genre_text)
            
            # Query vector DB for this genre
            results = self.movies_collection.query(
                query_embeddings=[genre_embedding],
                n_results=min(quota * 5, 100)  # Get 5× more than needed
            )
            
            # Fill quota, skip already-watched
            genre_recs = []
            for movie_id, distance in zip(results['ids'][0], results['distances'][0]):
                if movie_id not in watched_ids and movie_id not in seen_ids:
                    movie = self._get_movie_or_show(movie_id)
                    if movie:
                        similarity_score = (1 - distance) * 100
                        genre_recs.append(self._build_movie_dict(
                            movie, similarity_score, f"Because you like {genre}"
                        ))
                        if len(genre_recs) >= quota:
                            break
            
            buckets.append((genre, genre_recs))
        
        # Interleave: alternate between genre buckets
        recommendations = []
        for i in range(max(len(recs) for _, recs in buckets)):
            for genre, recs in buckets:
                if i < len(recs):
                    recommendations.append(recs[i])
                if len(recommendations) >= n_recommendations:
                    return recommendations
        
        return recommendations
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 7 — VECTOR STORE (Custom Implementation)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/recommendations/vector_store.py
# RAPPORT LOCATION: Chapter "IA" → "Stockage vectoriel"
# POINT: Custom-built vector database using numpy (avoids ChromaDB dependency)

```python
# FILE: recommendations/vector_store.py
import numpy as np
import pickle

class SimpleVectorStore:
    """
    Lightweight vector database using numpy cosine similarity.
    
    WHY CUSTOM? ChromaDB had compatibility issues on Windows.
    This replacement uses:
    - numpy arrays for embedding storage
    - cosine similarity for nearest-neighbor search
    - pickle files for persistence (saved to disk)
    
    PERFORMANCE: Handles thousands of movies efficiently.
    For very large catalogs (100k+), would need FAISS or AnnoyIndex.
    """
    
    def upsert(self, ids, embeddings, metadatas, documents):
        """
        Add or update documents in the store.
        If ID exists → update. If new → append.
        Saved to disk (.pkl file) after every update.
        """
        embeddings_array = np.array(embeddings)
        for i, doc_id in enumerate(ids):
            if doc_id in self.ids:
                idx = self.ids.index(doc_id)
                self.embeddings[idx] = embeddings_array[i]  # Update
            else:
                # Append new row to numpy array
                self.embeddings = np.vstack([self.embeddings, embeddings_array[i:i+1]])
                self.ids.append(doc_id)
                self.metadatas.append(metadatas[i])
        self._save()  # Persist to disk

    def query(self, query_embeddings, n_results=10, where=None):
        """
        Find most similar documents using cosine similarity.
        
        Math:
          similarity = dot(A, B) / (|A| × |B|)
          distance   = 1 - similarity
          
        Lower distance = more similar = better recommendation.
        
        Optional 'where' filter: {"genres": {"$contains": "Action"}}
        Filters metadatas before computing similarity.
        """
        query_vector = np.array(query_embeddings[0])
        
        # Compute cosine similarity against ALL stored embeddings (vectorized)
        similarities = np.dot(self.embeddings, query_vector) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vector)
        )
        distances = 1 - similarities
        
        # Apply metadata filters (genre, type, etc.)
        valid_indices = self._apply_filters(where)
        
        # Sort by distance, return top N
        valid_distances = distances[valid_indices]
        sorted_indices = np.argsort(valid_distances)[:n_results]
        
        return {
            'ids': [[self.ids[valid_indices[i]] for i in sorted_indices]],
            'distances': [[float(valid_distances[i]) for i in sorted_indices]]
        }
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 8 — REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/backend/urls.py
# RAPPORT LOCATION: Chapter "API REST" → "Documentation des endpoints"
# POINT: All 44 API routes — maps URLs to functionality

```
AUTHENTICATION
  POST /api/login/                          → JWT login (returns access + refresh tokens)
  POST /api/register/                       → Create new user account
  POST /api/password-reset/request/         → Send reset code to email
  POST /api/password-reset/verify-code/     → Verify 6-digit reset code
  POST /api/password-reset/reset/           → Set new password with verified code

MOVIES & CONTENT
  GET  /api/movies/                         → List movies (search, filter, paginate, sort)
  POST /api/movies/add/                     → Add new movie
  PUT  /api/movies/edit/<id>/               → Edit movie
  DELETE /api/movies/delete/<id>/           → Delete movie
  POST /api/movies/fetch/                   → Fetch from RapidAPI by year
  GET  /api/genres/                         → Get all unique genres
  GET  /api/omdb/search/?title=batman       → Search OMDb for movies
  POST /api/omdb/save-selected/             → Save selected OMDb results
  POST /api/external/browse/               → Fetch from any external API URL

PACKS (Themed Collections)
  GET  /api/packs/                          → List all packs with their movies
  POST /api/packs/                          → Create new pack
  GET  /api/packs/preview/?genres=Action    → Preview movies before creating pack
  GET/PUT/DELETE /api/packs/<id>/           → Get / Update / Delete a pack

USER FEATURES
  GET  /api/favorites/<username>/           → Get favorite movie IDs
  POST /api/favorites/<username>/           → Toggle favorite (add/remove)
  GET  /api/favorites/<username>/movies/    → Get full details of favorites
  GET  /api/watch-progress/?username=john   → Get all watch progress (0-100%)
  POST /api/watch-progress/update/          → Update watch progress for a movie

USER MANAGEMENT (Admin)
  GET  /api/users/                          → List all users
  DELETE /api/users/delete/<id>/            → Delete user

ANALYTICS (User Behavior Tracking)
  POST /api/analytics/track/               → Log a user activity
  POST /api/analytics/session/start/       → Start session when app opens
  POST /api/analytics/session/end/         → End session when app closes
  GET  /api/analytics/user/<username>/     → Get analytics for one user
  GET  /api/analytics/all/                 → Get analytics for all users (admin)
  GET  /api/analytics/continue-watching/<username>/  → Get Continue Watching list

AI RECOMMENDATIONS
  GET  /api/recommendations/health/        → Check AI system status
  POST /api/recommendations/index-movies/  → Index all movies into vector DB (admin)
  GET  /api/recommendations/<username>/    → Get personalized AI recommendations
  GET  /api/recommendations/similar/<id>/  → Get movies similar to a given movie
  GET  /api/recommendations/trending/      → Get trending/popular movies
  GET  /api/recommendations/sections/<username>/  → Get all 10 dashboard sections

PREFERENCES & AI LEARNING
  POST /api/preferences/update/            → Update user's favorite genres
  GET  /api/preferences/<username>/        → Get current preferences
  POST /api/dislikes/                       → Dislike a movie (hidden, affects AI)
  POST /api/analytics/recommendation-feedback/  → Track AI recommendation clicks
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 9 — MOVIES API VIEW (ListMoviesView)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/movies/views.py
# RAPPORT LOCATION: Chapter "API REST" → "Gestion des films"
# POINT: How the movie listing works with search, filters, sorting, and pagination

```python
# FILE: movies/views.py
class ListMoviesView(APIView):
    """
    GET /api/movies/?limit=24&page=1&search=batman&genre=Action&sort=year-desc
    
    Features:
    - Search: matches title AND genres simultaneously (Q OR query)
    - Filter: by type (Movie/TV Show) or genre
    - Sort: title-asc, title-desc, year-desc, year-asc
    - Pagination: limit + page parameters
    - Queries BOTH 'movies' and 'tv_shows' collections
    
    Response: {
      "movies": [...],
      "count": 24,
      "total": 1450,
      "page": 1,
      "limit": 24
    }
    """
    def get(self, request):
        limit  = int(request.GET.get('limit', 24))
        page   = int(request.GET.get('page', 1))
        search = request.GET.get('search', '').strip()
        filter_type  = request.GET.get('type', '').strip()
        filter_genre = request.GET.get('genre', '').strip()
        sort_by      = request.GET.get('sort', 'title-asc')

        # Search in both title AND genre fields at once
        if search:
            from mongoengine import Q
            search_filter = Q(title__icontains=search) | Q(listed_in__icontains=search)
        
        # Query both collections, combine results in Python
        items = []
        if not filter_type or 'movie' in filter_type.lower():
            items.extend(list(Movie.objects.filter(search_filter, ...)))
        if not filter_type or 'tv' in filter_type.lower():
            items.extend(list(TVShow.objects.filter(search_filter, ...)))

        # Sort combined list
        sort_map = {
            'title-asc':  lambda x: (x.title or '').lower(),
            'title-desc': lambda x: (x.title or '').lower(),
            'year-desc':  lambda x: x.release_year or 0,
            'year-asc':   lambda x: x.release_year or 0,
        }
        items.sort(key=sort_map[sort_by], reverse='desc' in sort_by)
        
        # Paginate
        offset = (page - 1) * limit
        paged_items = items[offset:offset + limit]
        
        return Response({
            "movies": [serialize(item) for item in paged_items],
            "total": len(items),
            "page": page,
            "limit": limit
        })
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 10 — DJANGO SETTINGS (Configuration)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/backend/settings.py
# RAPPORT LOCATION: Chapter "Environnement de développement" or "Configuration"
# POINT: How the project is configured — database, CORS, JWT, installed apps

```python
# FILE: backend/settings.py

# ── MongoDB Connection ───────────────────────────────────────────────────
import mongoengine
from dotenv import load_dotenv
load_dotenv()  # Load MONGO_URI from .env file (not committed to Git)

mongoengine.connect(
    db="MovieApp",
    host=os.getenv("MONGO_URI"),        # Connection string from .env
    tlsAllowInvalidCertificates=True    # For MongoDB Atlas dev connection
)
# Collections inside MongoDB: users, movies, tv_shows, favorites,
#   watch_progress, user_activities, user_preferences, user_sessions,
#   movie_watch_history, recommendation_feedback, packs

# ── SQLite (Django internals only) ───────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Only for admin sessions/migrations
    }
}

# ── Installed Apps ───────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.sessions',    # Admin session management
    'django.contrib.staticfiles', # Static file serving
    # Third-party
    'rest_framework',             # REST API framework
    'rest_framework_simplejwt',   # JWT token authentication
    'corsheaders',                # Allow Angular frontend to call API
    # Custom apps
    'accounts',                   # Users, auth, favorites, analytics
    'movies',                     # Movie/TV show management, packs
    'recommendations',            # AI recommendation engine
]

# ── REST Framework ────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # Every API call validates JWT token in "Authorization: Bearer <token>"
    )
}

# ── CORS (Frontend ↔ Backend Communication) ──────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True     # Dev: allow all; Prod: specify exact origins
CORS_ALLOW_CREDENTIALS = True     # Required for JWT Authorization header
CORS_ALLOW_HEADERS = [
    'authorization',              # Allows "Authorization: Bearer <token>"
    'content-type',
    'accept',
    # ... other standard headers
]

# ── JWT Tokens ────────────────────────────────────────────────────────────
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=1),   # Re-login after 1hr inactivity
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Stay logged in 7 days
    'ALGORITHM': 'HS256',                            # HMAC SHA-256 signing
    'SIGNING_KEY': SECRET_KEY,                       # Uses Django secret key
    'AUTH_HEADER_TYPES': ('Bearer',),               # "Authorization: Bearer ..."
}
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 11 — RECOMMENDATION API ENDPOINTS
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/recommendations/views.py + urls.py
# RAPPORT LOCATION: Chapter "IA" → "API de recommandation"
# POINT: How the Angular frontend requests recommendations from the AI engine

```python
# FILE: recommendations/views.py

# Singleton pattern — engine loads once (TensorFlow is heavy to init)
recommendation_engine = None
def get_engine():
    global recommendation_engine
    if recommendation_engine is None:
        recommendation_engine = RecommendationEngine()
    return recommendation_engine


@api_view(['GET'])
def get_recommendations(request, username):
    """
    GET /api/recommendations/john/?count=20&genre=Action&type=Movie
    
    Returns personalized AI recommendations:
    {
      "success": true,
      "username": "john",
      "count": 20,
      "recommendations": [
        {
          "movie_id": "507f1f77bcf86cd799439011",
          "title": "Inception",
          "type": "Movie",
          "genres": "Action, Sci-Fi, Thriller",
          "poster": "https://...",
          "similarity_score": 92.5,
          "reason": "Because you like Action"
        },
        ...
      ]
    }
    """
    engine = get_engine()
    count = int(request.GET.get('count', 10))
    filters = {}
    if request.GET.get('genre'): filters['genre'] = request.GET.get('genre')
    if request.GET.get('type'):  filters['type']  = request.GET.get('type')
    
    recommendations = engine.get_recommendations(
        username=username,
        n_recommendations=count,
        filters=filters or None
    )
    return Response({
        'success': True,
        'username': username,
        'count': len(recommendations),
        'recommendations': recommendations
    })


@api_view(['GET'])
def get_similar_movies(request, movie_id):
    """
    GET /api/recommendations/similar/abc123/?count=5
    Returns movies similar to given movie (content-based filtering)
    Used for "If you liked this, you'll love these" section
    """
    engine = get_engine()
    similar = engine.get_similar_movies(movie_id=movie_id,
                                         n_results=int(request.GET.get('count', 5)))
    return Response({'success': True, 'similar_movies': similar})


@api_view(['GET'])
def get_trending(request):
    """
    GET /api/recommendations/trending/?count=20
    Returns 2020+ content with IMDB rating ≥6.5 (movies) or ≥7.0 (shows)
    Sorted by IMDB rating (highest first)
    Excludes movies user has disliked
    """
    recent_movies = Movie.objects(release_year__gte=2020, imdb_rating__gte=6.5)\
                         .order_by('-imdb_rating', '-imdb_votes')
    # Filter dislikes, format response...
```

```
# FILE: recommendations/urls.py
urlpatterns = [
    path('health/',                           views.health_check),
    path('index-movies/',                     views.index_movies),
    path('trending/',                         views.get_trending),
    path('<str:username>/',                   views.get_recommendations),
    path('similar/<str:movie_id>/',           views.get_similar_movies),
    path('sections/<str:username>/',          views.get_personalized_sections),
    path('sections/<str:username>/regenerate/', views.regenerate_personalized_sections),
]
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 12 — DISLIKE SYSTEM (AI Penalty)
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/accounts/analytics_models.py (MovieDislike)
# RAPPORT LOCATION: Chapter "IA" → "Apprentissage continu"
# POINT: How dislikes are hidden from the user but actively used to improve AI

```python
# FILE: accounts/analytics_models.py (MovieDislike model)

class MovieDislike(Document):
    """
    HIDDEN dislike system — invisible to user but powerful for AI.
    
    When user dislikes a movie:
    1. Movie disappears from: recommendations, trending, packs, search
    2. AI receives penalty points (-5 to -20 if it was a recommendation)
    3. Genre scores are reduced in UserPreferences.recommendation_score
    4. Record saved here (user never sees it in UI — it's a background filter)
    
    Different from Favorites:
    - Favorites: VISIBLE to user, shown in favorites page
    - Dislikes: HIDDEN from user, silently affects all content visibility
    """
    username       = StringField(required=True)
    movie_id       = StringField(required=True)
    movie_title    = StringField()
    genres         = ListField(StringField())
    dislike_reason = StringField()  # "not-interested", "already-seen", etc.
    
    # AI Impact tracking
    was_ai_recommendation    = BooleanField(default=False)
    recommendation_position  = IntField()    # Which position AI placed it
    ai_penalty_score         = IntField(default=0)  # Points deducted
    
    # Filter settings (all True by default)
    hide_from_recommendations = BooleanField(default=True)
    hide_from_trending        = BooleanField(default=True)
    hide_from_search          = BooleanField(default=False)
    
    # Genre learning weights
    genre_penalty_weights = DictField()  # {"Action": -10, "Thriller": -5}
    
    meta = {
        'collection': 'movie_dislikes',
        'indexes': [{'fields': ['username', 'movie_id'], 'unique': True}]
    }
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 13 — PERSONALIZED DASHBOARD SECTIONS
# ═══════════════════════════════════════════════════════════════
# FILE: django project backend/recommendations/views.py (get_personalized_sections)
# RAPPORT LOCATION: Chapter "Interface utilisateur" → "Dashboard personnalisé"
# POINT: How the dashboard loads 10 different content sections tailored per user

```
The dashboard shows 10 sections, all personalized:

1.  AI Recommendations      — Movies chosen by the AI engine for this user
2.  Top Watched Movies       — Most-watched movies, sorted by user's genres first
3.  Top Watched Series       — Most-watched series, sorted by user's genres
4.  Top Searched Movies      — Most-searched movies across all users
5.  Top Searched Series      — Most-searched series
6.  Top 10 Movies            — Best rated/popular movies
7.  Top 10 Series            — Best rated/popular series
8.  Top 20 Favorites         — Most favorited content by all users
9.  Newly Added Movies       — Recently added to the database
10. Newly Added Series       — Recently added series

HOW PERSONALIZATION WORKS:
  - Same global data (e.g., "most watched movies" is same for all users)
  - But SORTED differently per user based on their preferred genres
  - User who likes "Action" sees Action movies first in each section
  - User who likes "Drama" sees Drama movies first in same sections
  - Stored in 'user_personalized_sections' MongoDB collection
  - Regenerated when: user changes preferences, watches new content

ENDPOINT: GET /api/recommendations/sections/{username}/
Returns all 10 sections with full movie details in one request.
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 14 — TECHNOLOGY STACK SUMMARY
# ═══════════════════════════════════════════════════════════════
# RAPPORT LOCATION: Chapter "Outils et technologies utilisés"
# POINT: Complete list of all technologies with their roles

```
BACKEND (Python)
  Django 5.2              — Web framework, URL routing, sessions
  Django REST Framework   — Build REST APIs with serializers, views
  djangorestframework-simplejwt  — JWT token authentication
  django-cors-headers     — Allow Angular frontend to call the API
  MongoEngine 0.29        — ODM (Object-Document Mapper) for MongoDB
  python-dotenv           — Load secrets from .env file
  requests                — HTTP calls to external APIs (OMDb, RapidAPI)

AI / MACHINE LEARNING
  TensorFlow 2.18         — Deep learning framework
  TensorFlow Hub 0.16     — Pre-trained model hub
  Universal Sentence Encoder v4  — Google's text embedding model (free, 512-dim)
  scikit-learn 1.9        — cosine_similarity utility
  numpy                   — Vector math for custom vector store

DATABASE
  MongoDB Atlas           — Cloud NoSQL database (primary app data)
  pymongo 4.10            — Low-level MongoDB driver
  SQLite                  — Django internal sessions (not app data)

FRONTEND (TypeScript)
  Angular 17              — SPA framework
  Angular Material        — UI component library
  RxJS                    — Reactive programming for API calls
  TypeScript              — Typed JavaScript
  Vite                    — Build tool (via ng serve)
  Node.js v22.22.3        — Runtime

EXTERNAL APIs
  OMDb API                — Movie details, posters (omdbapi.com)
  RapidAPI Netflix DB     — Bulk movie import by year
  TensorFlow Hub          — AI model download/loading

DEVELOPMENT TOOLS
  VS Code / Kiro          — IDE
  Postman                 — API testing
  MongoDB Compass         — Database visualization
```

---

*End of RAPPORT_CODE_REFERENCE.md*
*Generated: September 2026*
*Project: MovieHub — Plateforme de streaming avec recommandations IA*
