/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 MOVIE SERVICE - All Movie Operations and API Calls
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Central service for ALL movie-related operations:
    - Movie CRUD (Create, Read, Update, Delete)
    - Search and filtering
    - Favorites management
    - External API integration (OMDb, RapidAPI)
    - Packs management
    - User management (admin)
    - Genres listing

BACKEND CONNECTIONS:
    ALL methods connect to Django REST API (localhost:8000/api)
    See backend/urls.py for complete route list

AUTHENTICATION:
    - JWT token automatically added by auth.interceptor.ts
    - No need to manually add Authorization header
    - Some endpoints allow anonymous access

USED BY:
    - dashboard.component.ts → getMovies(), getPacks()
    - movie-details.component.ts → toggleFavorite()
    - admin.component.ts → All admin methods
    - search.component.ts → getMovies() with search params

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'  // Singleton service
})
export class MovieService {
  // ═══════════════════════════════════════════════════════════════════════
  // DEPENDENCIES & CONFIGURATION
  // ═══════════════════════════════════════════════════════════════════════
  private http = inject(HttpClient);
  private authService = inject(AuthService);  // Used for getting username
  private apiUrl = 'http://localhost:8000/api/movies';
  // Base URL for movie endpoints

  // ═══════════════════════════════════════════════════════════════════════
  // MOVIE LISTING & SEARCH
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Get movies with pagination, search, and filters
   * 
   * @param params - Query parameters object
   *   - limit: Number of movies per page (default: 24)
   *   - page: Page number (default: 1)
   *   - search: Search query (title, cast, director)
   *   - type: "Movie" or "TV Show" filter
   *   - genre: Genre filter (e.g., "Action")
   *   - sort: Sort order (e.g., "title-asc", "year-desc")
   * 
   * @returns Observable<any> - {movies: [...], count, total, page, limit}
   * 
   * BACKEND: GET /api/movies/ → ListMoviesView (movies/views.py)
   * 
   * USAGE EXAMPLES:
   *   // Get first page (24 movies)
   *   this.movieService.getMovies().subscribe(data => {
   *     this.movies = data.movies;
   *   });
   * 
   *   // Search for "batman"
   *   this.movieService.getMovies({search: 'batman'}).subscribe(...);
   * 
   *   // Get action movies, sorted by year
   *   this.movieService.getMovies({
   *     genre: 'Action',
   *     sort: 'year-desc',
   *     page: 2
   *   }).subscribe(...);
   * 
   * RESPONSE FORMAT:
   *   {
   *     movies: [{id, title, poster, release_year, ...}, ...],
   *     count: 24,  // Movies on this page
   *     total: 500, // Total movies matching filter
   *     page: 1,
   *     limit: 24
   *   }
   */
  getMovies(params: {
    limit?: number,
    page?: number,
    search?: string,
    type?: string,
    genre?: string,
    sort?: string
  } = {}): Observable<any> {
    // Destructure params with defaults
    const { limit = 24, page = 1, search = '', type = '', genre = '', sort = 'title-asc' } = params;
    
    // Build URL with query parameters
    let url = `${this.apiUrl}/?limit=${limit}&page=${page}&sort=${sort}`;
    
    // Add optional parameters if provided
    if (search) url += `&search=${encodeURIComponent(search)}`;
    // encodeURIComponent() = URL-safe encoding
    // Example: "action movies" → "action%20movies"
    
    if (type) url += `&type=${encodeURIComponent(type)}`;
    if (genre) url += `&genre=${encodeURIComponent(genre)}`;
    
    return this.http.get<any>(url);
  }

  /**
   * Get all unique genres from movies
   * 
   * @returns Observable<any> - {genres: ["Action", "Drama", ...]}
   * 
   * BACKEND: GET /api/genres/ → GenresView (movies/views.py)
   * 
   * HOW IT WORKS:
   *   1. Backend queries all movies
   *   2. Extracts 'listed_in' field (comma-separated genres)
   *   3. Splits and deduplicates
   *   4. Returns sorted genre list
   * 
   * USED FOR:
   *   - Genre filter dropdown
   *   - Genre tags on movie cards
   *   - Pack creation (select genres)
   */
  getGenres(): Observable<any> {
    return this.http.get<any>(`http://localhost:8000/api/genres/`);
  }

  /**
   * Search movies for suggestions (quick search)
   * 
   * @param query - Search query
   * @param page - Page number (default: 1)
   * @param limit - Results per page (default: 8)
   * @returns Observable<any> - {movies: [...], count, total}
   * 
   * USAGE: For real-time search suggestions in dropdown
   */
  searchMovies(query: string, page: number = 1, limit: number = 8): Observable<any> {
    return this.getMovies({ search: query, page, limit });
  }

  // ═══════════════════════════════════════════════════════════════════════
  // MOVIE CRUD OPERATIONS (Admin Only)
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Add new movie manually
   * 
   * @param movie - Movie object {title, type, release_year, director, ...}
   * @returns Observable<any> - {message, id}
   * 
   * BACKEND: POST /api/movies/add/ → AddMovieView (movies/views.py)
   * REQUIRES: Admin authentication
   * 
   * USAGE:
   *   this.movieService.addMovie({
   *     title: 'Inception',
   *     type: 'Movie',
   *     release_year: 2010,
   *     director: 'Christopher Nolan',
   *     cast: 'Leonardo DiCaprio, Tom Hardy',
   *     poster: 'https://...',
   *     description: '...'
   *   }).subscribe(response => {
   *     alert('Movie added! ID: ' + response.id);
   *   });
   */
  addMovie(movie: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/add/`, movie);
  }

  /**
   * Edit existing movie
   * 
   * @param movieId - Movie ID to edit
   * @param movie - Updated movie object
   * @returns Observable<any> - {message}
   * 
   * BACKEND: PUT /api/movies/edit/{movieId}/ → EditMovieView
   * REQUIRES: Admin authentication
   */
  editMovie(movieId: string, movie: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/edit/${movieId}/`, movie);
  }

  /**
   * Delete movie
   * 
   * @param movieId - Movie ID to delete
   * @returns Observable<any> - {message}
   * 
   * BACKEND: DELETE /api/movies/delete/{movieId}/ → DeleteMovieView
   * REQUIRES: Admin authentication
   * 
   * CAUTION: Permanent deletion from MongoDB
   */
  deleteMovie(movieId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/delete/${movieId}/`);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // EXTERNAL API INTEGRATION
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Fetch movies from external RapidAPI Netflix Database
   * 
   * @param year - Year to fetch (e.g., "2024")
   * @param type - "Movie" or "TV Show"
   * @returns Observable<any> - {message, count}
   * 
   * BACKEND: POST /api/movies/fetch/ → FetchMoviesView (movies/views.py)
   * 
   * WHAT IT DOES:
   *   1. Calls RapidAPI Netflix Database for specified year
   *   2. Fetches all movies/shows from that year
   *   3. Saves to MongoDB (prevents duplicates)
   *   4. Returns count of movies added
   * 
   * USAGE:
   *   // Fetch all 2024 movies
   *   this.movieService.fetchExternalMovies('2024', 'Movie')
   *     .subscribe(response => {
   *       alert(`Added ${response.count} movies`);
   *     });
   */
  fetchExternalMovies(year: string, type: string = 'Movie'): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/fetch/`, { year, type });
  }

  /**
   * Search OMDb API for movies
   * 
   * @param title - Movie title to search
   * @returns Observable<any> - {results: [{title, year, poster, already_saved}, ...]}
   * 
   * BACKEND: GET /api/omdb/search/?title={title} → ApiSearchOMDbView
   * 
   * WHAT IT DOES:
   *   1. Searches OMDb API (like IMDb database)
   *   2. Returns matching movies
   *   3. Checks which are already in our database (already_saved flag)
   * 
   * USAGE:
   *   this.movieService.searchOMDb('batman').subscribe(data => {
   *     this.searchResults = data.results;
   *     // Show results, grey out already saved movies
   *   });
   */
  searchOMDb(title: string): Observable<any> {
    return this.http.get<any>(`http://localhost:8000/api/omdb/search/?title=${encodeURIComponent(title)}`);
  }

  /**
   * Save selected movies from OMDb search results
   * 
   * @param items - Array of movies to save
   * @returns Observable<any> - {message, saved: [...], skipped: [...]}
   * 
   * BACKEND: POST /api/omdb/save-selected/ → ApiSaveSelectedOMDbView
   * 
   * USAGE:
   *   // User selects movies from search results
   *   const selected = searchResults.filter(m => m.selected);
   *   this.movieService.saveSelectedOMDb(selected).subscribe(response => {
   *     alert(`Saved ${response.saved.length} movies`);
   *   });
   */
  saveSelectedOMDb(items: any[]): Observable<any> {
    return this.http.post<any>(`http://localhost:8000/api/omdb/save-selected/`, { items });
  }

  /**
   * Browse any external API and import movies
   * 
   * @param apiUrl - Complete API URL to fetch from
   * @returns Observable<any> - {message, count}
   * 
   * BACKEND: POST /api/external/browse/ → ExternalApiBrowseView
   * 
   * WHAT IT DOES:
   *   - Fetches movies from ANY external API URL
   *   - Automatically paginate (up to 50 pages)
   *   - Saves to MongoDB
   * 
   * USAGE:
   *   this.movieService.browseExternalApi(
   *     'https://api.sampleapis.com/movies/action'
   *   ).subscribe(...);
   */
  browseExternalApi(apiUrl: string): Observable<any> {
    return this.http.post<any>(
      `http://localhost:8000/api/external/browse/`, 
      { api_url: apiUrl }
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // FAVORITES MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Get user's favorite movie IDs
   * 
   * @param username - Username
   * @returns Observable<any> - {username, favorites: ["id1", "id2", ...]}
   * 
   * BACKEND: GET /api/favorites/{username}/ → FavoritesView (accounts/views.py)
   * 
   * USED FOR:
   *   - Show heart icon on movie cards user has favorited
   *   - Check if movie is in favorites before toggling
   */
  getFavorites(username: string): Observable<any> {
    return this.http.get<any>(`http://localhost:8000/api/favorites/${username}/`);
  }

  /**
   * Get full movie details for user's favorites
   * 
   * @param username - Username
   * @returns Observable<any> - {username, count, movies: [{...}, ...]}
   * 
   * BACKEND: GET /api/favorites/{username}/movies/ → FavoriteMoviesView
   * 
   * USAGE:
   *   // Display user's favorites page
   *   this.movieService.getFavoriteMovies('john').subscribe(data => {
   *     this.favoriteMovies = data.movies;
   *   });
   */
  getFavoriteMovies(username: string): Observable<any> {
    return this.http.get<any>(`http://localhost:8000/api/favorites/${username}/movies/`);
  }

  /**
   * Toggle favorite (add if not favorited, remove if favorited)
   * 
   * @param username - Username
   * @param movieId - Movie ID
   * @returns Observable<any> - {username, is_favorite, favorites: [...]}
   * 
   * BACKEND: POST /api/favorites/{username}/ → FavoritesView
   * 
   * HOW IT WORKS:
   *   1. Backend checks if Favorite document exists
   *   2. If exists: Delete it (unfavorite)
   *   3. If not exists: Create it (favorite)
   *   4. Returns is_favorite: true/false
   * 
   * USAGE:
   *   // User clicks heart icon
   *   toggleFavorite(movieId: string) {
   *     const username = this.authService.getUsername()!;
   *     this.movieService.toggleFavorite(username, movieId)
   *       .subscribe(response => {
   *         this.isFavorite = response.is_favorite;
   *       });
   *   }
   */
  toggleFavorite(username: string, movieId: string): Observable<any> {
    return this.http.post<any>(`http://localhost:8000/api/favorites/${username}/`, { movie_id: movieId });
  }

  // ═══════════════════════════════════════════════════════════════════════
  // USER MANAGEMENT (Admin Only)
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Get all users (admin dashboard)
   * 
   * @returns Observable<any> - {users: [{id, user_id, username, email, role}, ...]}
   * 
   * BACKEND: GET /api/users/ → ListUsersView (accounts/views.py)
   * REQUIRES: Admin authentication
   */
  getUsers(): Observable<any> {
    return this.http.get<any>(`http://localhost:8000/api/users/`);
  }

  /**
   * Delete user (admin only, can't delete admin)
   * 
   * @param userId - User ID to delete
   * @returns Observable<any> - {message}
   * 
   * BACKEND: DELETE /api/users/delete/{userId}/ → DeleteUserView
   * REQUIRES: Admin authentication
   */
  deleteUser(userId: string): Observable<any> {
    return this.http.delete<any>(`http://localhost:8000/api/users/delete/${userId}/`);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PACKS MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Get all movie packs
   * 
   * @returns Observable<any> - {packs: [{id, name, genres, years, movie_count}, ...]}
   * 
   * BACKEND: GET /api/packs/ → PackListView (movies/views.py)
   * 
   * PACKS = Themed collections like "Action Movies 2024"
   * 
   * USAGE:
   *   // Display packs as horizontal scrolling sections
   *   this.movieService.getPacks().subscribe(data => {
   *     this.packs = data.packs;
   *   });
   */
  getPacks(): Observable<any> {
    return this.http.get<any>(`http://localhost:8000/api/packs/`);
  }

  /**
   * Preview pack movies before creating (admin)
   * 
   * @param genres - Array of genres ["Action", "Sci-Fi"]
   * @param years - Array of years [2023, 2024]
   * @returns Observable<any> - {count, movies: [...]}
   * 
   * BACKEND: GET /api/packs/preview/?genres=Action&years=2023,2024 → PackPreviewView
   * 
   * USAGE:
   *   // Show admin how many movies will be in pack before creating
   *   this.movieService.previewPack(['Action'], [2024]).subscribe(data => {
   *     alert(`This pack will have ${data.count} movies`);
   *   });
   */
  previewPack(genres: string[], years: number[]): Observable<any> {
    const g = genres.join(',');
    const y = years.join(',');
    return this.http.get<any>(`http://localhost:8000/api/packs/preview/?genres=${encodeURIComponent(g)}&years=${encodeURIComponent(y)}`);
  }

  /**
   * Create new pack (admin)
   * 
   * @param pack - Pack object {name, genres, years, movie_ids, cover_image, ...}
   * @returns Observable<any> - {message, id}
   * 
   * BACKEND: POST /api/packs/ → PackListView
   */
  createPack(pack: any): Observable<any> {
    return this.http.post<any>(`http://localhost:8000/api/packs/`, pack);
  }

  /**
   * Update existing pack (admin)
   * 
   * @param packId - Pack ID
   * @param pack - Updated pack object
   * @returns Observable<any> - {message}
   * 
   * BACKEND: PUT /api/packs/{packId}/ → PackDetailView
   */
  updatePack(packId: string, pack: any): Observable<any> {
    return this.http.put<any>(`http://localhost:8000/api/packs/${packId}/`, pack);
  }

  /**
   * Delete pack (admin)
   * 
   * @param packId - Pack ID
   * @returns Observable<any> - {message}
   * 
   * BACKEND: DELETE /api/packs/{packId}/ → PackDetailView
   */
  deletePack(packId: string): Observable<any> {
    return this.http.delete<any>(`http://localhost:8000/api/packs/${packId}/`);
  }
}

/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 MOVIE SERVICE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MOVIE OPERATIONS:
    getMovies(params) → List with pagination/search/filters
    getGenres() → All unique genres
    addMovie(movie) → Admin adds movie
    editMovie(id, movie) → Admin edits movie
    deleteMovie(id) → Admin deletes movie

EXTERNAL APIs:
    fetchExternalMovies(year, type) → RapidAPI Netflix Database
    searchOMDb(title) → Search OMDb API
    saveSelectedOMDb(items) → Save from OMDb results
    browseExternalApi(url) → Import from any API

FAVORITES:
    getFavorites(username) → Get favorite IDs
    getFavoriteMovies(username) → Get full favorite movies
    toggleFavorite(username, movieId) → Add/remove favorite

USER MANAGEMENT (Admin):
    getUsers() → List all users
    deleteUser(userId) → Delete user

PACKS:
    getPacks() → List all packs
    previewPack(genres, years) → Preview before creating
    createPack(pack) → Create new pack
    updatePack(id, pack) → Update pack
    deletePack(id) → Delete pack

AUTHENTICATION:
    All methods automatically get JWT token from auth.interceptor.ts
    No manual Authorization header needed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/
