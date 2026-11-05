"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 MOVIES MODELS - Movie & TV Show Data Structures (MongoDB Collections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Defines the structure of movie, TV show, and pack data in MongoDB.
    These models describe what information is stored for each movie/show.

MODELS IN THIS FILE:
    1. Movie - Individual movie documents
    2. TVShow - TV show documents (same structure as Movie)
    3. Pack - Themed movie collections/bundles

MONGODB COLLECTIONS CREATED:
    - 'movies' collection → Stores Movie documents
    - 'tv_shows' collection → Stores TVShow documents
    - 'packs' collection → Stores Pack documents

WHY SEPARATE COLLECTIONS?
    Movies and TV shows have same fields but stored separately for:
    - Better organization
    - Easier filtering (e.g., "only movies" or "only shows")
    - But queried together when displaying to users

RELATED FILES:
    - movies/views.py → Uses these models to CRUD operations
    - accounts/models.py → Favorite and WatchProgress reference movie_id
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from mongoengine import Document, StringField, IntField, ListField, FloatField


# ═══════════════════════════════════════════════════════════════════════════
# MODEL 1: Movie (Individual Movies)
# ═══════════════════════════════════════════════════════════════════════════
# MongoDB Collection: 'movies'
# Purpose: Store movie information fetched from external APIs or added manually
# Used By: ListMoviesView, FetchMoviesView, AddMovieView in movies/views.py
# ═══════════════════════════════════════════════════════════════════════════
class Movie(Document):
    # ─────────────────────────────────────────────────────────────────────
    # MOVIE FIELDS - What data each movie document contains
    # ─────────────────────────────────────────────────────────────────────
    
    show_id = StringField()
    # External API ID (e.g., IMDb ID like "tt1375666")
    # Used to:
    #   - Prevent duplicate movies when fetching from API
    #   - Link to external sources for more info
    #   - Fetch additional data (ratings, reviews)
    
    title = StringField()
    # Movie title (e.g., "Inception", "The Dark Knight")
    # Used for:
    #   - Display in UI
    #   - Search functionality
    #   - Sorting
    
    type = StringField()
    # Content type (usually "Movie")
    # Distinguishes from TV shows when both collections queried together
    
    director = StringField()
    # Director name (e.g., "Christopher Nolan")
    # Can be multiple directors separated by comma
    # Example: "Anthony Russo, Joe Russo"
    
    cast = StringField()
    # Comma-separated actor names
    # Example: "Leonardo DiCaprio, Tom Hardy, Ellen Page"
    # Used for search (users can search by actor name)
    
    country = StringField()
    # Country/countries of origin
    # Example: "USA" or "USA, UK"
    # Used for filtering by region
    
    release_year = IntField()
    # Year movie was released (e.g., 2010)
    # Integer type allows:
    #   - Easy sorting (newest first, oldest first)
    #   - Range filtering (e.g., 2020-2024)
    #   - Year-based pack creation
    
    rating = StringField()
    # Age/content rating (e.g., "PG-13", "R", "G", "TV-MA")
    # Helps users find age-appropriate content
    # Also used for parental controls
    
    duration = StringField()
    # Movie length as string (e.g., "148 min", "2h 28min")
    # String format because different sources format differently
    # Used for display in movie details
    
    listed_in = StringField()
    # Comma-separated genres (e.g., "Action, Sci-Fi, Thriller")
    # IMPORTANT: This field is split and used for:
    #   - Genre filtering (user selects "Action")
    #   - Genre search (search includes genre matches)
    #   - Creating genre-based packs
    # Example processing:
    #   Stored: "Action, Sci-Fi, Thriller"
    #   Split to: ["Action", "Sci-Fi", "Thriller"]
    
    primary_category = StringField()
    # Primary/main genre category for the movie
    # Single genre that best represents the movie (e.g., "Action", "Horror", "Drama")
    # Used by AI for primary recommendation filtering
    # Displayed with distinct color in UI (different from secondary genres)
    # If empty, automatically set to first genre from listed_in
    
    description = StringField()
    # Movie plot summary/overview
    # Text can be long (500+ characters)
    # Displayed in movie detail page
    # Used for search (matching keywords in description)
    
    poster = StringField()
    # Poster image URL (e.g., "https://image.tmdb.org/t/p/w500/abc123.jpg")
    # If None/empty: Frontend shows placeholder image
    # Fetched from:
    #   - OMDb API (poster field)
    #   - RapidAPI (poster field)
    #   - Manual upload
    # Image sizes usually: 500x750px or similar aspect ratio
    
    imdb_rating = FloatField(default=0.0)
    # IMDB rating score (0.0 to 10.0)
    # Example: 8.8 for "The Dark Knight"
    # Used for:
    #   - Sorting by quality (highest rated first)
    #   - Netflix-style recommendations (prioritize high-rated)
    #   - Display in UI (show rating badge)
    #   - Filtering (e.g., show only 8.0+ rated movies)
    
    imdb_votes = IntField(default=0)
    # Number of IMDB user votes
    # Example: 2,500,000 votes for popular movies
    # Used for:
    #   - Popularity metric (more votes = more popular)
    #   - Weighting ratings (10.0 with 10 votes < 8.5 with 1M votes)
    #   - Tie-breaking when ratings are same

    meta = {
        'collection': 'movies'
        # MongoDB collection name
        # All Movie documents stored here
    }

    def __str__(self):
        # String representation for debugging and admin panel
        # Returns movie title
        return self.title
    
    # Example MongoDB Document:
    # {
    #     "_id": ObjectId("507f1f77bcf86cd799439011"),
    #     "show_id": "tt1375666",
    #     "title": "Inception",
    #     "type": "Movie",
    #     "director": "Christopher Nolan",
    #     "cast": "Leonardo DiCaprio, Tom Hardy, Ellen Page",
    #     "country": "USA, UK",
    #     "release_year": 2010,
    #     "rating": "PG-13",
    #     "duration": "148 min",
    #     "listed_in": "Action, Sci-Fi, Thriller",
    #     "description": "A thief who steals corporate secrets...",
    #     "poster": "https://..."
    # }


# ═══════════════════════════════════════════════════════════════════════════
# MODEL 2: TVShow (TV Series)
# ═══════════════════════════════════════════════════════════════════════════
# MongoDB Collection: 'tv_shows'
# Purpose: Store TV show information (same structure as Movie)
# Why Separate: Organization, easier filtering, but queried together with movies
# Used By: Same views as Movie (ListMoviesView, etc.)
# ═══════════════════════════════════════════════════════════════════════════
class TVShow(Document):
    """
    TV Show model - identical structure to Movie
    
    Stored in separate collection because:
        1. Organization - Keep movies and shows separated in database
        2. Performance - Can query just shows or just movies efficiently
        3. Future expansion - Shows might need extra fields (seasons, episodes)
    
    But displayed together:
        - ListMoviesView queries both 'movies' and 'tv_shows'
        - Frontend displays them in same list
        - User can filter to see only one type
    """
    
    # ─────────────────────────────────────────────────────────────────────
    # TV SHOW FIELDS (Identical to Movie)
    # ─────────────────────────────────────────────────────────────────────
    
    show_id = StringField()
    # Same as Movie.show_id
    
    title = StringField()
    # Show title (e.g., "Breaking Bad", "Stranger Things")
    
    type = StringField(default='TV Show')
    # Default value is 'TV Show' to distinguish from movies
    # Automatically set when document created
    
    director = StringField()
    # For shows, this might be creator/showrunner
    # Example: "Vince Gilligan" for Breaking Bad
    
    cast = StringField()
    # Main cast members
    # Example: "Bryan Cranston, Aaron Paul, Anna Gunn"
    
    country = StringField()
    # Country of production
    
    release_year = IntField()
    # Year show first aired
    
    rating = StringField()
    # TV rating (e.g., "TV-MA", "TV-14")
    
    duration = StringField()
    # For shows, might be:
    #   - "1 Season" / "5 Seasons"
    #   - "50 min" (episode length)
    # Depends on source API
    
    listed_in = StringField()
    # Genres (same as Movie)
    
    primary_category = StringField()
    # Primary/main genre category for the TV show
    # Single genre that best represents the show (e.g., "Drama", "Comedy", "Thriller")
    # Used by AI for primary recommendation filtering
    # Displayed with distinct color in UI (different from secondary genres)
    # If empty, automatically set to first genre from listed_in
    
    description = StringField()
    # Show synopsis
    
    poster = StringField()
    # Show poster/cover image
    
    imdb_rating = FloatField(default=0.0)
    # IMDB rating score (0.0 to 10.0)
    # Example: 9.5 for "Breaking Bad"
    # Used for:
    #   - Sorting by quality (highest rated first)
    #   - Netflix-style recommendations (prioritize high-rated series)
    #   - Display in UI (show rating badge)
    #   - Filtering (e.g., show only 8.5+ rated series)
    
    imdb_votes = IntField(default=0)
    # Number of IMDB user votes
    # Example: 2,000,000+ votes for popular series
    # Used for:
    #   - Popularity metric (more votes = more popular)
    #   - Weighting ratings (9.0 with 100 votes < 8.5 with 500K votes)
    #   - Tie-breaking when ratings are same

    meta = {
        'collection': 'tv_shows'
        # Separate collection from movies
    }

    def __str__(self):
        return self.title


# ═══════════════════════════════════════════════════════════════════════════
# MODEL 3: Pack (Themed Movie Collections)
# ═══════════════════════════════════════════════════════════════════════════
# MongoDB Collection: 'packs'
# Purpose: Group movies/shows into themed collections (like Netflix categories)
# Used By: PackListView, PackDetailView in movies/views.py
# ═══════════════════════════════════════════════════════════════════════════
class Pack(Document):
    """
    Movie Packs - Themed collections of movies/shows
    
    Use Cases:
        - "Action Movies 2024" - All action movies from 2024
        - "Christopher Nolan Collection" - All Nolan movies
        - "Top Rated Thrillers" - Curated thriller selection
        - "Oscar Winners" - Award-winning movies
    
    Pack Creation:
        1. Admin creates pack via /api/packs/ (POST)
        2. Specifies criteria:
           - By genres (e.g., ["Action", "Sci-Fi"])
           - By years (e.g., [2020, 2021, 2022])
           - By specific movie IDs (handpicked movies)
        3. Frontend displays pack as horizontal scroll section
    
    Display Order:
        Packs shown in order of 'level' field
        level=1 → Shown at top
        level=2 → Shown below level 1
        etc.
    """
    
    # ─────────────────────────────────────────────────────────────────────
    # PACK FIELDS
    # ─────────────────────────────────────────────────────────────────────
    
    name = StringField(required=True)
    # Pack name shown to users
    # Example: "Action Heroes 2024", "Sci-Fi Classics"
    # required=True → Must have a name
    
    genres = ListField(StringField())
    # List of genres to filter by
    # Example: ["Drama", "Horror"]
    # Empty list = no genre filter
    # Used to auto-populate pack with matching movies
    # 
    # How it works:
    #   genres=["Action"] → Finds all movies with "Action" in listed_in
    
    years = ListField(IntField())
    # List of years to filter by
    # Example: [2023, 2024, 2025]
    # Empty list = no year filter
    # 
    # How it works:
    #   years=[2024] → Finds all movies with release_year=2024
    
    movie_ids = ListField(StringField())
    # Specific movie/show IDs to include
    # Example: ["507f1f77bcf86cd799439011", "507f191e810c19729de860ea"]
    # Used for handpicked/curated collections
    # Admin can manually select exact movies to include
    # 
    # Priority:
    #   If movie_ids provided: Only shows these movies
    #   If empty: Uses genre/year filters to find movies
    
    level = IntField(default=1)
    # Display priority (1 = highest priority, shown first)
    # default=1 → New packs shown at top
    # 
    # Example order on homepage:
    #   level=1: "Trending Now" (top)
    #   level=2: "New Releases" (below)
    #   level=3: "Action Movies" (below that)
    # 
    # Admin can reorder by changing level numbers
    
    cover_image = StringField()
    # Pack cover/banner image URL
    # Larger than movie posters (e.g., 1920x400px)
    # Example: "https://image.server.com/pack_banner.jpg"
    # Can be:
    #   - URL (most common)
    #   - Base64 encoded image (for small images)
    
    cover_height = IntField(default=250)
    # Banner height in pixels
    # Range: 150px to 450px
    # default=250 → Medium-sized banner
    # 
    # Different packs can have different heights:
    #   Featured pack: 400px (large)
    #   Regular pack: 250px (medium)
    #   Small pack: 150px (compact)
    
    cover_position = StringField(default='center')
    # Vertical focal point alignment for cover image
    # Options: 'top', 'center', 'bottom'
    # default='center' → Shows center of image
    # 
    # Example use:
    #   Image has text at top → cover_position='top'
    #   Image has action at bottom → cover_position='bottom'
    
    cover_fit = StringField(default='contain')
    # How image fits in banner area
    # Options:
    #   'contain' → Show full image (may have letterboxing)
    #   'cover' → Fill entire area (may crop image)
    # default='contain' → Shows complete image
    # 
    # Visual difference:
    #   contain: |----[IMAGE]----| (black bars if aspect ratio different)
    #   cover:   |[IMAGE FILLS]|  (may crop top/bottom or sides)

    meta = {
        'collection': 'packs',
        'ordering': ['level']
        # Default sort order when querying packs
        # Automatically sorts by level (1, 2, 3...)
        # So level=1 packs come first
    }

    def __str__(self):
        # String representation
        return self.name
    
    # Example MongoDB Document:
    # {
    #     "_id": ObjectId("..."),
    #     "name": "Action Heroes 2024",
    #     "genres": ["Action", "Adventure"],
    #     "years": [2024],
    #     "movie_ids": [],  # Empty = use genre/year filter
    #     "level": 1,
    #     "cover_image": "https://example.com/banner.jpg",
    #     "cover_height": 300,
    #     "cover_position": "center",
    #     "cover_fit": "cover"
    # }


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MODELS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODEL       COLLECTION      PURPOSE                     TYPICAL COUNT
────────────────────────────────────────────────────────────────────────────
Movie       'movies'        Individual movies           1000s of documents
TVShow      'tv_shows'      TV series                   100s of documents
Pack        'packs'         Themed collections          10-50 documents

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 SEARCH & FILTER FIELDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIELD           SEARCHABLE  FILTERABLE  SORTABLE  NOTES
────────────────────────────────────────────────────────────────────────────
title           ✓           ✗           ✓         Main search field
listed_in       ✓           ✓           ✗         Genres (comma-separated)
release_year    ✗           ✓           ✓         Year filtering & sorting
director        ✓           ✗           ✗         Search by director
cast            ✓           ✗           ✗         Search by actor
type            ✗           ✓           ✗         Movie vs TV Show

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 DATA SOURCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Movies and TV shows are populated from:
    1. RapidAPI Netflix Database (FetchMoviesView)
       - Fetches by year
       - POST /api/movies/fetch/

    2. OMDb API (ApiSearchOMDbView, ApiSaveSelectedOMDbView)
       - Search by title
       - GET /api/omdb/search/?title=batman
       - POST /api/omdb/save-selected/

    3. Any External API (ExternalApiBrowseView)
       - Provide any API URL
       - POST /api/external/browse/

    4. Manual Entry (AddMovieView)
       - Admin can manually add movies
       - POST /api/movies/add/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""