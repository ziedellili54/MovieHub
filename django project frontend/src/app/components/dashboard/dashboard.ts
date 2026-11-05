import { Component, OnInit, inject, ChangeDetectorRef, ChangeDetectionStrategy, NgZone, ApplicationRef } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { MovieService } from '../../services/movie.service';
import { AnalyticsService } from '../../services/analytics.service';
import { RecommendationService } from '../../services/recommendation.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  imports: [FormsModule, CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class DashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private movieService = inject(MovieService);
  private analyticsService = inject(AnalyticsService);
  private recommendationService = inject(RecommendationService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private appRef = inject(ApplicationRef);

  username = '';
  isAdmin = false;
  movies: any[] = [];
  filteredMovies: any[] = [];
  users: any[] = [];
  loading = false;
  successMessage = '';
  errorMessage = '';

  // Continue Watching
  continueWatchingMovies: any[] = [];
  loadingContinueWatching = false;

  // AI Recommendations
  recommendedMovies: any[] = [];
  loadingRecommendations = false;
  
  // Trending & Popular Movies
  trendingMovies: any[] = [];
  loadingTrending = false;

  // NEW: Personalized Sections (10 sections)
  topWatchedMovies: any[] = [];
  topWatchedSeries: any[] = [];
  topSearchedMovies: any[] = [];
  topSearchedSeries: any[] = [];
  top10Movies: any[] = [];
  top10Series: any[] = [];
  top20Favorites: any[] = [];
  newlyAddedMovies: any[] = [];
  newlyAddedSeries: any[] = [];
  loadingAllSections = false;

  // Filters & Search
  searchQuery = '';
  selectedGenre = '';
  selectedType = '';
  sortBy = 'title-asc';
  genresList: string[] = [];

  // Pagination
  currentPage = 1;
  itemsPerPage = 12;  // Show 12 movies per page
  totalMovies = 0;
  totalPages = 0;

  // Form states
  fetchYear = '2020';
  fetchType = 'TV Show';
  posterInputType: 'url' | 'file' = 'url';
  newMovie = {
    title: '',
    type: 'Movie',
    release_year: new Date().getFullYear(),
    director: '',
    cast: '',
    country: '',
    rating: '',
    duration: '',
    listed_in: '',
    description: '',
    poster: ''
  };

  // OMDb Search & Select state
  omdbSearchQuery = '';
  omdbResults: any[] = [];
  omdbSearching = false;
  omdbSaving = false;

  // Packs state
  packs: any[] = [];
  filteredPacks: any[] = [];
  packPreviewResults: any[] = [];
  packPreviewing = false;
  packSaving = false;
  editingPack: any = null;
  packBuilder = {
    name: '',
    level: 1,
    coverImage: '',
    coverHeight: 250,
    coverPosition: 'center',
    coverFit: 'contain',
    selectedGenres: [] as string[],
    selectedYears: [] as number[],
    selectedMovieIds: [] as string[]
  };
  openedPackModal: any = null;

  // Editing state
  editingMovie: any = null;

  // Selected movie for detail modal
  selectedMovieForDetail: any = null;
  showMovieModal = false; // ✅ Extra flag to force modal visibility
  
  // Similar movies for detail modal
  similarMovies: any[] = [];
  loadingSimilar = false;
  
  // Movie watch progress - stores watching_percentage from backend
  movieProgress: { [key: string]: number } = {};
  movieWatchingPercentage: { [key: string]: number } = {};  // User-editable percentages
  
  // User's favorite genres for AI feedback tracking
  favoriteGenres: string[] = [];

  // Years array from 2026 down to 1950
  yearsList: number[] = Array.from({ length: 2026 - 1950 + 1 }, (_, i) => 2026 - i);

  // Favorites/Wishlist
  favorites: Set<string> = new Set();
  showFavoritesOnly = false;

  // Hero/Featured movie
  featuredMovie: any = null;

  // Active view for user navigation
  activeView: 'home' | 'movies' | 'tv' | 'favorites' = 'home';
  
  // Combined search query (searches both name and genre)
  combinedSearchQuery = '';

  // Admin panel visibility
  showAdminPanel = false;

  // Carousel scroll state for each pack
  packScrollPositions: { [key: string]: number } = {};
  ITEMS_PER_PAGE = 5;  // Show 5 movies at a time
  MAX_PACK_ITEMS = 100;  // Max 100 movies per pack
  
  // Get visible items for carousel (5 at a time)
  getCarouselItems(packId: string, allItems: any[]): any[] {
    const position = this.packScrollPositions[packId] || 0;
    const maxItems = Math.min(allItems.length, this.MAX_PACK_ITEMS);
    const limitedItems = allItems.slice(0, maxItems);
    const start = position * this.ITEMS_PER_PAGE;
    const end = start + this.ITEMS_PER_PAGE;
    return limitedItems.slice(start, end);
  }
  
  // Check if can scroll left
  canScrollLeft(packId: string): boolean {
    return (this.packScrollPositions[packId] || 0) > 0;
  }
  
  // Check if can scroll right
  canScrollRight(packId: string, allItems: any[]): boolean {
    const position = this.packScrollPositions[packId] || 0;
    const maxItems = Math.min(allItems.length, this.MAX_PACK_ITEMS);
    const totalPages = Math.ceil(maxItems / this.ITEMS_PER_PAGE);
    return position < totalPages - 1;
  }
  
  // Scroll left (previous 5 movies)
  scrollPackLeft(packId: string) {
    if (this.canScrollLeft(packId)) {
      this.packScrollPositions[packId] = (this.packScrollPositions[packId] || 0) - 1;
      this.cdr.detectChanges();
    }
  }
  
  // Scroll right (next 5 movies)
  scrollPackRight(packId: string, allItems: any[]) {
    if (this.canScrollRight(packId, allItems)) {
      this.packScrollPositions[packId] = (this.packScrollPositions[packId] || 0) + 1;
      this.cdr.detectChanges();
    }
  }
  
  // Navigate to pack full view
  viewAllPack(packName: string, packType: 'ai' | 'trending' | 'continue' | 'custom', packId?: string) {
    console.log(`View all: ${packName} (${packType})`, packId);
    
    // Store pack data for detail page
    if (packType === 'ai') {
      localStorage.setItem('packView', JSON.stringify({
        name: packName,
        type: packType,
        movies: this.recommendedMovies
      }));
    } else if (packType === 'trending') {
      localStorage.setItem('packView', JSON.stringify({
        name: packName,
        type: packType,
        movies: this.trendingMovies
      }));
    } else if (packType === 'continue') {
      localStorage.setItem('packView', JSON.stringify({
        name: packName,
        type: packType,
        movies: this.continueWatchingMovies
      }));
    } else if (packType === 'custom' && packId) {
      const pack = this.packs.find(p => p.id === packId);
      if (pack) {
        localStorage.setItem('packView', JSON.stringify({
          name: pack.name,
          type: packType,
          movies: pack.movies,
          level: pack.level,
          genres: pack.genres
        }));
      }
    }
    
    // Navigate to pack detail view
    this.showPackDetail = true;
    this.loadPackDetail();
    this.cdr.detectChanges();
  }
  
  // Pack detail view state
  showPackDetail = false;
  packDetailData: any = null;
  
  // Load pack detail
  loadPackDetail() {
    const data = localStorage.getItem('packView');
    if (data) {
      this.packDetailData = JSON.parse(data);
      this.filteredMovies = this.packDetailData.movies || [];
      this.totalMovies = this.filteredMovies.length;
      this.totalPages = Math.ceil(this.totalMovies / this.itemsPerPage);
    }
  }
  
  // Close pack detail
  closePackDetail() {
    this.showPackDetail = false;
    this.packDetailData = null;
    this.activeView = 'home';
    localStorage.removeItem('packView');
    this.loadMovies();
    this.cdr.detectChanges();
  }
  
  // Go back to previous view (for navigation)
  goBackToPreviousView() {
    if (this.showPackDetail) {
      // If in pack detail, close it
      this.closePackDetail();
    } else if (this.selectedMovieForDetail) {
      // If movie modal is open, close it
      this.closeMovieDetail();
    } else if (this.activeView !== 'home') {
      // If not on home, go to home
      this.setActiveView('home');
    } else {
      // Default: go to home
      this.setActiveView('home');
    }
    this.cdr.detectChanges();
  }
  Math = Math;
  private searchDebounce: any = null;
  
  // Search dropdown state
  searchFocused = false;
  showAllGenres = false;
  searchSuggestions: any[] = [];
  loadingSuggestions = false;

  onSearchInput() {
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => {
      // Track search activity
      if (this.searchQuery.trim()) {
        this.analyticsService.trackSearch(this.username, this.searchQuery, this.filteredMovies.length);
      }
      this.applyFilters();
    }, 300);
  }
  
  // Combined search for name AND genre
  onCombinedSearch() {
    clearTimeout(this.searchDebounce);
    
    // Get search suggestions in real-time
    const query = this.combinedSearchQuery.trim();
    if (query.length >= 2) {
      this.loadSearchSuggestions(query);
    } else {
      this.searchSuggestions = [];
    }
    
    // Debounced search for filtering main content
    this.searchDebounce = setTimeout(() => {
      // Set search query from combined input
      this.searchQuery = this.combinedSearchQuery.trim();
      
      // Track search if there's a query
      if (this.searchQuery) {
        this.analyticsService.trackSearch(this.username, this.searchQuery, this.filteredMovies.length);
        console.log('🔍 Searching for:', this.searchQuery);
      } else {
        console.log('🔍 Search cleared, showing all movies');
      }
      
      // Reset to page 1 and reload movies with search
      this.currentPage = 1;
      this.loadMovies();
    }, 300);
  }
  
  loadSearchSuggestions(query: string) {
    this.loadingSuggestions = true;
    this.movieService.searchMovies(query, 1, 8).subscribe({
      next: (res) => {
        this.searchSuggestions = (res && res.movies) ? res.movies : [];
        this.loadingSuggestions = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading search suggestions:', err);
        this.searchSuggestions = [];
        this.loadingSuggestions = false;
        this.cdr.detectChanges();
      }
    });
  }
  
  selectSearchSuggestion(movie: any) {
    this.searchFocused = false;
    this.searchSuggestions = [];
    this.combinedSearchQuery = '';
    this.openMovieDetail(movie);
  }
  
  clearSearch() {
    this.searchQuery = '';
    this.combinedSearchQuery = '';
    this.searchSuggestions = [];
    this.currentPage = 1;
    this.loadMovies();
  }

  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
      return;
    }
    this.username = this.authService.getUsername() || 'User';
    this.isAdmin = this.authService.isAdmin();
    
    // ✅ PREVENT BROWSER BACK BUTTON FROM GOING TO LOGIN
    history.pushState(null, '', location.href);
    window.onpopstate = () => {
      history.pushState(null, '', location.href);
      
      if (this.showPackDetail) {
        this.closePackDetail();
      } else if (this.selectedMovieForDetail) {
        this.closeMovieDetail();
      } else if (this.activeView !== 'home') {
        this.setActiveView('home');
      }
    };
    
    // ✅ FORCE CHANGE DETECTION ON EVERY CLICK (to fix modal not showing)
    document.addEventListener('click', () => {
      this.ngZone.run(() => {
        this.cdr.detectChanges();
      });
    });
    
    this.analyticsService.trackAppOpen(this.username);
    
    const savedFavorites = localStorage.getItem('favorites');
    if (savedFavorites) {
      this.favorites = new Set(JSON.parse(savedFavorites));
    }
    
    const packView = localStorage.getItem('packView');
    if (packView) {
      this.showPackDetail = true;
      this.loadPackDetail();
    }
    
    this.loadGenres();
    this.loadFavorites();
    this.loadPacks();
    this.loadMovies();
    this.loadContinueWatching();
    this.loadAllSections();
    this.loadTrending();
    
    if (this.isAdmin) {
      this.loadUsers();
    }
  }

  setFeaturedMovie() {
    // Only set once - don't change if already set
    if (this.featuredMovie) {
      console.log('🎬 Featured movie already set, keeping:', this.featuredMovie?.title);
      return;
    }
    
    // Priority 1: Use trending movies (newest releases) - Pick FIRST (not random) from top trending
    if (this.trendingMovies.length > 0) {
      this.featuredMovie = this.trendingMovies[0];  // Always use first trending movie
      console.log('🎬 Featured movie from trending:', this.featuredMovie?.title, this.featuredMovie?.release_year);
    }
    // Priority 2: Use AI recommendations - Pick FIRST (not random)
    else if (this.recommendedMovies.length > 0) {
      this.featuredMovie = this.recommendedMovies[0];  // Always use first recommended movie
      console.log('🎬 Featured movie from AI recommendations:', this.featuredMovie?.title);
    }
    // Priority 3: Use newest movie from catalog (2020+)
    else if (this.movies.length > 0) {
      // Filter for recent movies only (2020+)
      const currentYear = new Date().getFullYear();
      const recentMovies = this.movies.filter(m => m.release_year >= 2020);
      
      if (recentMovies.length > 0) {
        // Sort by year descending and pick random from top 10
        recentMovies.sort((a, b) => (b.release_year || 0) - (a.release_year || 0));
        const top10 = recentMovies.slice(0, Math.min(10, recentMovies.length));
        const randomIndex = Math.floor(Math.random() * top10.length);
        this.featuredMovie = top10[randomIndex];
        console.log('🎬 Featured movie (newest from catalog):', this.featuredMovie?.title, this.featuredMovie?.release_year);
      } else {
        // Last resort: pick random from all movies
        const randomIndex = Math.floor(Math.random() * this.movies.length);
        this.featuredMovie = this.movies[randomIndex];
        console.log('🎬 Featured movie (fallback):', this.featuredMovie?.title);
      }
    }
  }

  // Method to refresh the featured movie (can be called anytime)
  refreshFeaturedMovie() {
    this.setFeaturedMovie();
    this.cdr.detectChanges();
  }

  setActiveView(view: 'home' | 'movies' | 'tv' | 'favorites') {
    this.activeView = view;
    
    // Reset filters and pagination
    this.currentPage = 1;
    this.searchQuery = '';
    
    switch(view) {
      case 'home':
        this.selectedType = '';
        this.showFavoritesOnly = false;
        this.loadMovies();
        break;
      case 'movies':
        this.selectedType = 'Movie';
        this.showFavoritesOnly = false;
        this.applyFilters();
        break;
      case 'tv':
        this.selectedType = 'TV Show';
        this.showFavoritesOnly = false;
        this.applyFilters();
        break;
      case 'favorites':
        this.showFavoritesOnly = true;
        this.loadFavoriteMovies();
        break;
    }
    
    this.cdr.detectChanges();
  }

  loadMovies() {
    this.loading = true;
    const searchParam = this.searchQuery ? this.searchQuery.trim() : '';
    
    console.log('📡 Loading movies with params:', {
      page: this.currentPage,
      limit: this.itemsPerPage,
      search: searchParam,
      type: this.selectedType,
      genre: this.selectedGenre
    });
    
    this.movieService.getMovies({
      page: this.currentPage,
      limit: this.itemsPerPage,
      search: searchParam,
      type: this.selectedType || '',
      genre: this.selectedGenre || '',
      sort: this.sortBy || 'title-asc'
    }).subscribe({
      next: (res) => {
        console.log('✅ API Response:', res);
        this.movies = (res && res.movies) ? res.movies : [];
        this.filteredMovies = this.movies;
        this.totalMovies = (res && typeof res.total === 'number') ? res.total : 0;
        this.totalPages = Math.ceil(this.totalMovies / this.itemsPerPage) || 1;
        
        console.log(`📊 Loaded ${this.movies.length} movies, total: ${this.totalMovies}`);
        
        // Always set/refresh featured movie when movies load
        this.setFeaturedMovie();
        
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('❌ Error loading movies:', err);
        this.errorMessage = 'Failed to load movies catalog.';
        this.movies = [];
        this.filteredMovies = [];
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadContinueWatching() {
    if (!this.username) return;
    
    this.loadingContinueWatching = true;
    this.analyticsService.getContinueWatching(this.username).subscribe({
      next: (res) => {
        if (res && res.movies) {
          this.continueWatchingMovies = res.movies;
          console.log(`📺 Continue Watching: ${this.continueWatchingMovies.length} movies`);
          
          // Store watching percentages in local state for quick access
          this.continueWatchingMovies.forEach(movie => {
            const movieId = movie.id;
            if (movieId && movie.watching_percentage) {
              this.movieWatchingPercentage[movieId] = movie.watching_percentage;
            }
          });
        }
        this.loadingContinueWatching = false;
        
        // ✅ Force immediate UI update
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading continue watching:', err);
        this.loadingContinueWatching = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadRecommendations() {
    if (!this.username) return;
    
    this.loadingRecommendations = true;
    this.recommendationService.getRecommendations(this.username, 100).subscribe({
      next: (res) => {
        if (res && res.success && res.recommendations) {
          this.recommendedMovies = res.recommendations.slice(0, 100);
          console.log(`⭐ Recommendations: ${this.recommendedMovies.length} movies`);
          
          // Update featured movie with recommendation
          this.setFeaturedMovie();
        } else {
          this.recommendedMovies = [];
        }
        this.loadingRecommendations = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading recommendations:', err);
        this.recommendedMovies = [];
        this.loadingRecommendations = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadTrending() {
    this.loadingTrending = true;
    this.recommendationService.getTrending(100, undefined, this.username).subscribe({
      next: (res) => {
        if (res && res.success && res.trending) {
          this.trendingMovies = res.trending.slice(0, 100);
          console.log(`🔥 Trending: ${this.trendingMovies.length} movies`);
          
          // Update featured movie with trending
          this.setFeaturedMovie();
        } else {
          this.trendingMovies = [];
        }
        this.loadingTrending = false;
        
        // ✅ Force immediate UI update
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading trending:', err);
        this.trendingMovies = [];
        this.loadingTrending = false;
        this.cdr.detectChanges();
      }
    });
  }

  // NEW: Load all 10 personalized sections at once
  loadAllSections() {
    if (!this.username) return;
    
    // ✅ Set loading flags for AI recommendations section (NOT trending, that's separate)
    this.loadingAllSections = true;
    this.loadingRecommendations = true;
    console.log('Loading all personalized sections...');
    
    this.recommendationService.getAllSections(this.username).subscribe({
      next: (res) => {
        if (res && res.success && res.sections) {
          // Section 1: AI Recommendations
          if (res.sections.ai_recommendations && res.sections.ai_recommendations.movies) {
            this.recommendedMovies = res.sections.ai_recommendations.movies;
            console.log(`AI Recommendations: ${this.recommendedMovies.length} items`);
          }
          
          // Section 2: Top Watched Movies
          if (res.sections.top_watched_movies && res.sections.top_watched_movies.movies) {
            this.topWatchedMovies = res.sections.top_watched_movies.movies;
            console.log(`Top Watched Movies: ${this.topWatchedMovies.length} items`);
          }
          
          // Section 3: Top Watched Series
          if (res.sections.top_watched_series && res.sections.top_watched_series.movies) {
            this.topWatchedSeries = res.sections.top_watched_series.movies;
            console.log(`Top Watched Series: ${this.topWatchedSeries.length} items`);
          }
          
          // Section 4: Top Searched Movies
          if (res.sections.top_searched_movies && res.sections.top_searched_movies.movies) {
            this.topSearchedMovies = res.sections.top_searched_movies.movies;
            console.log(`Top Searched Movies: ${this.topSearchedMovies.length} items`);
          }
          
          // Section 5: Top Searched Series
          if (res.sections.top_searched_series && res.sections.top_searched_series.movies) {
            this.topSearchedSeries = res.sections.top_searched_series.movies;
            console.log(`Top Searched Series: ${this.topSearchedSeries.length} items`);
          }
          
          // Section 6: Top 10 Movies
          if (res.sections.top_10_movies && res.sections.top_10_movies.movies) {
            this.top10Movies = res.sections.top_10_movies.movies;
            console.log(`Top 10 Movies: ${this.top10Movies.length} items`);
          }
          
          // Section 7: Top 10 Series
          if (res.sections.top_10_series && res.sections.top_10_series.movies) {
            this.top10Series = res.sections.top_10_series.movies;
            console.log(`Top 10 Series: ${this.top10Series.length} items`);
          }
          
          // Section 8: Top 20 Favorites
          if (res.sections.top_20_favorites && res.sections.top_20_favorites.movies) {
            this.top20Favorites = res.sections.top_20_favorites.movies;
            console.log(`Top 20 Favorites: ${this.top20Favorites.length} items`);
          }
          
          // Section 9: Newly Added Movies
          if (res.sections.newly_added_movies && res.sections.newly_added_movies.movies) {
            this.newlyAddedMovies = res.sections.newly_added_movies.movies;
            console.log(`Newly Added Movies: ${this.newlyAddedMovies.length} items`);
          }
          
          // Section 10: Newly Added Series
          if (res.sections.newly_added_series && res.sections.newly_added_series.movies) {
            this.newlyAddedSeries = res.sections.newly_added_series.movies;
            console.log(`Newly Added Series: ${this.newlyAddedSeries.length} items`);
          }
          
          // Update featured movie
          this.setFeaturedMovie();
          
          console.log('All sections loaded successfully!');
        }
        
        // ✅ Clear loading flags for AI recommendations
        this.loadingAllSections = false;
        this.loadingRecommendations = false;
        
        // ✅ Force immediate UI update
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading all sections:', err);
        
        // ✅ Clear loading flags on error
        this.loadingAllSections = false;
        this.loadingRecommendations = false;
        
        // Fallback to old method if new endpoint fails
        this.loadRecommendations();
        this.cdr.detectChanges();
      }
    });
  }

  loadGenres() {
    this.movieService.getGenres().subscribe({
      next: (res) => {
        const allGenres = (res && res.genres) ? res.genres : [];
        // Filter out types (Movie, TV Show, etc.) and keep only actual genres
        const typesToExclude = ['movie', 'movies', 'tv show', 'tv shows', 'film', 'films', 'serie', 'series', 'tv', 'show', 'shows'];
        this.genresList = allGenres.filter((genre: string) => 
          !typesToExclude.includes(genre.toLowerCase().trim())
        );
        console.log(`📊 Loaded ${this.genresList.length} genres (filtered out types)`);
      },
      error: (err) => {
        console.error('Error loading genres:', err);
      }
    });
  }

  extractGenres() {
    // Genres are loaded from backend via loadGenres()
  }

  loadFavorites() {
    if (!this.username) return;
    this.movieService.getFavorites(this.username).subscribe({
      next: (res) => {
        this.favorites = new Set(res.favorites || []);
        localStorage.setItem(`favorites_${this.username}`, JSON.stringify(Array.from(this.favorites)));
        if (this.showFavoritesOnly) {
          this.applyFavoritesFilterLocally();
        }
      },
      error: () => {
        const saved = localStorage.getItem(`favorites_${this.username}`);
        if (saved) {
          this.favorites = new Set(JSON.parse(saved));
        }
      }
    });
  }

  applyFavoritesFilterLocally() {
    // Use the dedicated API endpoint instead of filtering local paginated data
    this.loadFavoriteMovies();
  }

  loadFavoriteMovies() {
    // Use the new dedicated favorites API endpoint
    if (!this.username || this.favorites.size === 0) {
      this.filteredMovies = [];
      this.totalMovies = 0;
      this.totalPages = 1;
      this.currentPage = 1;
      this.cdr.detectChanges();
      return;
    }
    this.loading = true;
    this.movieService.getFavoriteMovies(this.username).subscribe({
      next: (res) => {
        this.filteredMovies = (res && res.movies) ? res.movies : [];
        this.totalMovies = this.filteredMovies.length;
        this.totalPages = 1;
        this.currentPage = 1;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading favorite movies:', err);
        this.filteredMovies = [];
        this.totalMovies = 0;
        this.totalPages = 1;
        this.currentPage = 1;
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  applyFilters() {
    this.applyPackFiltersLocally();
    
    if (this.selectedGenre) {
      this.analyticsService.trackCategoryVisit(this.username, this.selectedGenre, [this.selectedGenre]);
    }
    
    if (this.showFavoritesOnly) {
      this.applyFavoritesFilterLocally();
      return;
    }
    this.currentPage = 1;
    this.loadMovies();
  }

  applyPackFiltersLocally() {
    if (!this.selectedGenre) {
      this.filteredPacks = [...this.packs];
    } else {
      this.filteredPacks = this.packs.filter(pack => {
        return pack.genres && pack.genres.includes(this.selectedGenre);
      });
    }
  }

  loadUsers() {
    this.movieService.getUsers().subscribe({
      next: (res) => {
        this.users = (res && res.users) ? res.users : [];
      },
      error: (err) => {
        console.error('Error loading users:', err);
      }
    });
  }

  // ─── PACK methods ──────────────────────────────────────
  loadPacks() {
    this.movieService.getPacks().subscribe({
      next: (res) => {
        this.packs = (res && res.packs) ? res.packs : [];
        this.applyPackFiltersLocally();
        this.cdr.detectChanges();
      },
      error: () => { 
        this.packs = []; 
        this.applyPackFiltersLocally(); 
      }
    });
  }

  toggleGenreSelection(genre: string) {
    const idx = this.packBuilder.selectedGenres.indexOf(genre);
    if (idx >= 0) this.packBuilder.selectedGenres.splice(idx, 1);
    else this.packBuilder.selectedGenres.push(genre);
  }

  toggleYearSelection(year: number) {
    const idx = this.packBuilder.selectedYears.indexOf(year);
    if (idx >= 0) this.packBuilder.selectedYears.splice(idx, 1);
    else this.packBuilder.selectedYears.push(year);
  }

  isGenreSelected(genre: string) { return this.packBuilder.selectedGenres.includes(genre); }
  isYearSelected(year: number) { return this.packBuilder.selectedYears.includes(year); }

  togglePackPreviewItem(item: any) {
    const idx = this.packBuilder.selectedMovieIds.indexOf(item.id);
    if (idx >= 0) this.packBuilder.selectedMovieIds.splice(idx, 1);
    else this.packBuilder.selectedMovieIds.push(item.id);
  }

  isPackItemSelected(id: string) { return this.packBuilder.selectedMovieIds.includes(id); }

  onSelectAllPackItems() {
    if (this.packBuilder.selectedMovieIds.length === this.packPreviewResults.length) {
      this.packBuilder.selectedMovieIds = [];
    } else {
      this.packBuilder.selectedMovieIds = this.packPreviewResults.map(r => r.id);
    }
    this.cdr.detectChanges();
  }

  onPreviewPack() {
    if (!this.packBuilder.selectedGenres.length && !this.packBuilder.selectedYears.length) return;
    this.packPreviewing = true;
    this.packPreviewResults = [];
    this.packBuilder.selectedMovieIds = [];
    this.movieService.previewPack(this.packBuilder.selectedGenres, this.packBuilder.selectedYears).subscribe({
      next: (res) => {
        this.packPreviewResults = res.results || [];
        this.packPreviewing = false;
        this.cdr.detectChanges();
      },
      error: () => { this.packPreviewing = false; }
    });
  }

  onPackCoverFileSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.packBuilder.coverImage = e.target.result;
        this.cdr.detectChanges();
      };
      reader.readAsDataURL(file);
    }
  }

  selectPosterAsPackCover(posterUrl: string) {
    if (posterUrl) {
      this.packBuilder.coverImage = posterUrl;
      this.cdr.detectChanges();
    }
  }

  openPackModal(pack: any, event?: Event) {
    if (event) {
      event.stopPropagation();
    }
    this.openedPackModal = pack;
    this.cdr.detectChanges();
  }

  closePackModal(event?: Event) {
    if (event && event.target !== event.currentTarget) {
      return;
    }
    this.openedPackModal = null;
    this.cdr.detectChanges();
  }

  onSavePack() {
    if (!this.packBuilder.name.trim() || !this.packBuilder.selectedMovieIds.length) return;
    this.packSaving = true;
    const payload = {
      name: this.packBuilder.name.trim(),
      genres: this.packBuilder.selectedGenres,
      years: this.packBuilder.selectedYears,
      movie_ids: this.packBuilder.selectedMovieIds,
      level: this.packBuilder.level,
      cover_image: this.packBuilder.coverImage,
      cover_height: this.packBuilder.coverHeight,
      cover_position: this.packBuilder.coverPosition,
      cover_fit: this.packBuilder.coverFit
    };
    const req = this.editingPack
      ? this.movieService.updatePack(this.editingPack.id, payload)
      : this.movieService.createPack(payload);

    req.subscribe({
      next: (res) => {
        this.successMessage = res.message;
        this.packSaving = false;
        this.editingPack = null;
        this.resetPackBuilder();
        this.loadPacks();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to save pack.';
        this.packSaving = false;
        this.cdr.detectChanges();
      }
    });
  }

  onEditPack(pack: any) {
    this.editingPack = pack;
    this.packBuilder = {
      name: pack.name,
      level: pack.level,
      coverImage: pack.cover_image || '',
      coverHeight: pack.cover_height || 250,
      coverPosition: pack.cover_position || 'center',
      coverFit: pack.cover_fit || 'contain',
      selectedGenres: [...(pack.genres || [])],
      selectedYears: [...(pack.years || [])],
      selectedMovieIds: [...(pack.movie_ids || [])]
    };
    this.packPreviewResults = pack.movies || [];
    this.cdr.detectChanges();
    // Scroll to builder
    setTimeout(() => document.getElementById('pack-builder-card')?.scrollIntoView({ behavior: 'smooth' }), 100);
  }

  onDeletePack(packId: string, packName: string) {
    if (!confirm(`Delete pack "${packName}"? This cannot be undone.`)) return;
    this.movieService.deletePack(packId).subscribe({
      next: (res) => {
        this.successMessage = res.message;
        this.loadPacks();
      },
      error: (err) => { this.errorMessage = err.error?.error || 'Failed to delete pack.'; }
    });
  }

  onMovePackLevel(pack: any, direction: 'up' | 'down') {
    const newLevel = direction === 'up' ? pack.level - 1 : pack.level + 1;
    if (newLevel < 1) return;
    this.movieService.updatePack(pack.id, { ...pack, level: newLevel }).subscribe({
      next: () => this.loadPacks(),
      error: () => {}
    });
  }

  resetPackBuilder() {
    this.packBuilder = { name: '', level: 1, coverImage: '', coverHeight: 250, coverPosition: 'center', coverFit: 'contain', selectedGenres: [], selectedYears: [], selectedMovieIds: [] };
    this.packPreviewResults = [];
  }

  cancelEditPack() {
    this.editingPack = null;
    this.resetPackBuilder();
  }
  // ─────────────────────────────────────────────────────

  // Handle image loading errors - fallback to clean SVG poster
  onImageError(event: any) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450"><rect width="100%" height="100%" fill="#1a1a26"/><text x="50%" y="48%" fill="#ffae00" font-size="20" font-weight="bold" font-family="sans-serif" text-anchor="middle">MovieHub</text><text x="50%" y="54%" fill="#64748b" font-size="14" font-family="sans-serif" text-anchor="middle">No Image Available</text></svg>`;
    event.target.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }

  // Get secondary genres (excluding primary category)
  getSecondaryGenres(movie: any): string[] {
    if (!movie.listed_in) return [];
    
    const allGenres = movie.listed_in.split(',').map((g: string) => g.trim());
    const primary = movie.primary_category || allGenres[0];
    
    // Return genres excluding the primary one, limit to 2
    return allGenres.filter((g: string) => g !== primary).slice(0, 2);
  }

  // Get primary genre for display
  getPrimaryGenre(movie: any): string {
    return movie.primary_category || (movie.listed_in ? movie.listed_in.split(',')[0].trim() : '');
  }

  // Format IMDB vote count (1500000 → "1.5M", 50000 → "50K")
  formatVotes(votes: number): string {
    if (!votes || votes === 0) return '';
    
    if (votes >= 1000000) {
      return (votes / 1000000).toFixed(1).replace('.0', '') + 'M';
    } else if (votes >= 1000) {
      return (votes / 1000).toFixed(0) + 'K';
    } else {
      return votes.toString();
    }
  }

  // Generate movie poster URL
  getPosterUrl(movie: any): string {
    // If movie has poster URL from database and it's valid, use it
    if (movie.poster && movie.poster !== 'N/A') {
      // If poster starts with http, use it as-is (external CDN)
      if (movie.poster.startsWith('http')) {
        return movie.poster;
      }
      // If poster starts with / (local path), prepend backend URL
      if (movie.poster.startsWith('/')) {
        return 'http://localhost:8000' + movie.poster;
      }
      return movie.poster;
    }
    
    // Generate unique fallback poster for each movie
    const title = movie.title || 'Movie';
    const type = movie.type || 'Film';
    const year = movie.release_year || '';
    const genre = movie.listed_in ? movie.listed_in.split(',')[0].trim() : '';
    
    // Escape special characters for SVG
    const escapeXml = (str: string) => {
      return str.replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&apos;');
    };
    
    const safeTitle = escapeXml(title.length > 35 ? title.substring(0, 32) + '...' : title);
    const safeGenre = escapeXml(genre.length > 25 ? genre.substring(0, 22) + '...' : genre);
    
    // Generate unique color scheme based on title hash
    const hashCode = (str: string) => {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash = hash & hash;
      }
      return Math.abs(hash);
    };
    
    const hash = hashCode(title);
    const styleIndex = hash % 6; // 6 different styles
    
    let gradientDef = '';
    let background = '';
    let accentColor = '';
    let pattern = '';
    
    // 6 unique gradient styles
    switch(styleIndex) {
      case 0: // Red to Purple
        gradientDef = `<linearGradient id="grad${hash}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#8B0000;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#4B0082;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1a1a2e;stop-opacity:1" />
        </linearGradient>`;
        background = `url(#grad${hash})`;
        accentColor = '#ff4757';
        pattern = `<circle cx="50" cy="80" r="100" fill="#ff4757" opacity="0.05"/>
                   <circle cx="250" cy="370" r="120" fill="#4B0082" opacity="0.05"/>`;
        break;
      case 1: // Blue to Cyan
        gradientDef = `<linearGradient id="grad${hash}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#003366;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#006699;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#0a0e27;stop-opacity:1" />
        </linearGradient>`;
        background = `url(#grad${hash})`;
        accentColor = '#00d9ff';
        pattern = `<rect x="-20" y="200" width="340" height="2" fill="#00d9ff" opacity="0.2"/>
                   <rect x="-20" y="250" width="340" height="2" fill="#00d9ff" opacity="0.2"/>`;
        break;
      case 2: // Orange to Red
        gradientDef = `<linearGradient id="grad${hash}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#ff6b00;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#e50914;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1a0a0e;stop-opacity:1" />
        </linearGradient>`;
        background = `url(#grad${hash})`;
        accentColor = '#ffa500';
        pattern = `<circle cx="150" cy="100" r="80" fill="none" stroke="#ffa500" stroke-width="1" opacity="0.2"/>
                   <circle cx="150" cy="100" r="100" fill="none" stroke="#ffa500" stroke-width="1" opacity="0.15"/>`;
        break;
      case 3: // Green to Teal
        gradientDef = `<linearGradient id="grad${hash}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#0f4c3a;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#1e7a6d;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#0a1a1a;stop-opacity:1" />
        </linearGradient>`;
        background = `url(#grad${hash})`;
        accentColor = '#00ff88';
        pattern = `<polygon points="0,0 300,0 250,80" fill="#00ff88" opacity="0.05"/>
                   <polygon points="300,450 0,450 50,370" fill="#00ff88" opacity="0.05"/>`;
        break;
      case 4: // Purple to Pink
        gradientDef = `<linearGradient id="grad${hash}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#6a0572;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#a8206b;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1a0a1a;stop-opacity:1" />
        </linearGradient>`;
        background = `url(#grad${hash})`;
        accentColor = '#ff00ff';
        pattern = `<circle cx="80" cy="380" r="60" fill="#ff00ff" opacity="0.08"/>
                   <circle cx="220" cy="70" r="70" fill="#a8206b" opacity="0.08"/>`;
        break;
      case 5: // Navy to Steel
        gradientDef = `<linearGradient id="grad${hash}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1e3a5f;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#2c5f8d;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#0f1419;stop-opacity:1" />
        </linearGradient>`;
        background = `url(#grad${hash})`;
        accentColor = '#4dabf7';
        pattern = `<rect x="0" y="0" width="150" height="450" fill="#4dabf7" opacity="0.03"/>
                   <rect x="150" y="0" width="150" height="450" fill="#2c5f8d" opacity="0.03"/>`;
        break;
    }
    
    // Beautiful unique gradient poster
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
      <defs>
        ${gradientDef}
      </defs>
      
      <!-- Background -->
      <rect width="300" height="450" fill="${background}"/>
      
      <!-- Decorative patterns -->
      ${pattern}
      
      <!-- Film icon with unique color -->
      <circle cx="150" cy="160" r="65" fill="${accentColor}" opacity="0.15"/>
      <text x="150" y="180" font-family="Arial, sans-serif" font-size="55" fill="${accentColor}" text-anchor="middle" opacity="0.9">🎬</text>
      
      <!-- Info Box -->
      <rect x="15" y="260" width="270" height="160" rx="12" fill="rgba(0,0,0,0.7)" stroke="${accentColor}" stroke-width="2" opacity="0.9"/>
      
      <!-- Title -->
      <text x="150" y="295" font-family="Arial, sans-serif" font-size="17" font-weight="bold" fill="#ffffff" text-anchor="middle">${safeTitle}</text>
      
      <!-- Divider line -->
      <line x1="40" y1="310" x2="260" y2="310" stroke="${accentColor}" stroke-width="2" opacity="0.5"/>
      
      <!-- Type and Year -->
      <text x="150" y="335" font-family="Arial, sans-serif" font-size="14" fill="#e2e8f0" text-anchor="middle">${type}${year ? ' • ' + year : ''}</text>
      
      <!-- Genre -->
      ${safeGenre ? `<text x="150" y="360" font-family="Arial, sans-serif" font-size="13" fill="${accentColor}" font-weight="600" text-anchor="middle">${safeGenre}</text>` : ''}
      
      <!-- Bottom accent -->
      <rect x="15" y="385" width="270" height="4" rx="2" fill="${accentColor}" opacity="0.6"/>
      
      <!-- MovieHub branding -->
      <text x="150" y="410" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle" font-weight="600">MovieHub</text>
    </svg>`;
    
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }

  getTimeRemaining(watchPercentage: number): string {
    // Calculate remaining time based on percentage
    // Assuming average movie is 120 minutes (2 hours)
    const avgMovieDuration = 120;
    const remainingPercentage = 100 - watchPercentage;
    const remainingMinutes = Math.round((remainingPercentage / 100) * avgMovieDuration);
    
    if (remainingMinutes < 60) {
      return `${remainingMinutes} min`;
    } else {
      const hours = Math.floor(remainingMinutes / 60);
      const minutes = remainingMinutes % 60;
      return minutes > 0 ? `${hours}h ${minutes}min` : `${hours}h`;
    }
  }

  getAIMatchScore(score: number): number {
    // Convert similarity score (0-1) to percentage (0-100)
    return Math.round(score * 100);
  }

  getMatchColor(score: number): string {
    // Color based on AI match percentage
    const percentage = this.getAIMatchScore(score);
    if (percentage >= 85) return '#00ff88'; // Green - Excellent match
    if (percentage >= 70) return '#ffae00'; // Orange - Good match
    return '#ff6b6b'; // Red - Decent match
  }

  onFetchMovies() {
    if (!this.fetchYear) return;
    this.loading = true;
    this.movieService.fetchExternalMovies(this.fetchYear, this.fetchType).subscribe({
      next: (res) => {
        this.successMessage = res.message;
        this.loadMovies();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to fetch titles from external API.';
        this.loading = false;
      }
    });
  }

  isAddFormValid(): boolean {
    // Only Title is truly required — all other fields have defaults or are optional
    return !!(this.newMovie.title && this.newMovie.title.trim());
  }

  onPosterFileSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.newMovie.poster = e.target.result;
        this.cdr.detectChanges();
      };
      reader.readAsDataURL(file);
    }
  }

  removePoster() {
    this.newMovie.poster = '';
    this.cdr.detectChanges();
  }

  onAddMovie() {
    if (!this.isAddFormValid()) return;
    this.loading = true;
    this.movieService.addMovie(this.newMovie).subscribe({
      next: () => {
        this.successMessage = `Successfully added "${this.newMovie.title}"`;
        this.newMovie = {
          title: '',
          type: 'Movie',
          release_year: new Date().getFullYear(),
          director: '',
          cast: '',
          country: '',
          rating: '',
          duration: '',
          listed_in: '',
          description: '',
          poster: ''
        };
        this.posterInputType = 'url';
        this.loadMovies();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to add movie.';
        this.loading = false;
      }
    });
  }

  // OMDb API Search & Tick-to-Save methods
  trackByShowId(index: number, item: any): string {
    return item.show_id || item.title;
  }

  toggleOmdbItem(item: any) {
    if (item.already_saved) return;
    item.selected = !item.selected;
    this.cdr.detectChanges();
  }

  onSearchOMDb() {
    if (!this.omdbSearchQuery.trim()) return;
    this.omdbSearching = true;
    this.errorMessage = '';
    this.movieService.searchOMDb(this.omdbSearchQuery.trim()).subscribe({
      next: (res) => {
        this.omdbResults = (res && res.results) ? res.results.map((r: any) => ({ ...r, selected: false })) : [];
        if (this.omdbResults.length === 0) {
          this.errorMessage = 'No results found on OMDb for that title.';
        }
        this.omdbSearching = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to search OMDb API.';
        this.omdbSearching = false;
        this.cdr.detectChanges();
      }
    });
  }

  hasSelectedOMDbItems(): boolean {
    return this.omdbResults.some(r => r.selected && !r.already_saved);
  }

  onSaveSelectedOMDb() {
    const selected = this.omdbResults.filter(r => r.selected && !r.already_saved);
    if (selected.length === 0) return;
    
    this.omdbSaving = true;
    this.movieService.saveSelectedOMDb(selected).subscribe({
      next: (res) => {
        let msg = '';
        if (res.saved && res.saved.length > 0) {
          msg += `✓ Successfully added to database: ${res.saved.join(', ')}. `;
        }
        if (res.skipped && res.skipped.length > 0) {
          msg += `⚠️ Skipped (already in database): ${res.skipped.join(', ')}.`;
        }
        this.successMessage = msg || res.message || 'Operation completed successfully.';
        this.omdbResults = [];
        this.omdbSearchQuery = '';
        this.omdbSaving = false;
        this.loadMovies();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to save selected items to database.';
        this.omdbSaving = false;
        this.cdr.detectChanges();
      }
    });
  }

  onDeleteMovie(movieId: string) {
    if (!confirm('Are you sure you want to delete this movie?')) return;
    this.loading = true;
    this.movieService.deleteMovie(movieId).subscribe({
      next: (res) => {
        this.successMessage = res.message || 'Movie deleted successfully';
        this.loadMovies();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to delete movie.';
        this.loading = false;
      }
    });
  }

  onStartEditMovie(movie: any) {
    this.editingMovie = { ...movie };
  }

  onSaveEditMovie() {
    if (!this.editingMovie || !this.editingMovie.title) return;
    this.loading = true;
    this.movieService.editMovie(this.editingMovie.id, this.editingMovie).subscribe({
      next: (res) => {
        this.successMessage = res.message || 'Movie updated successfully';
        this.editingMovie = null;
        this.loadMovies();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to update movie.';
        this.loading = false;
      }
    });
  }

  onCancelEditMovie() {
    this.editingMovie = null;
  }

  onDeleteUser(userId: string) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    this.movieService.deleteUser(userId).subscribe({
      next: (res) => {
        this.successMessage = res.message || 'User deleted successfully';
        this.loadUsers();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to delete user.';
      }
    });
  }

  onLogout() {
    // End analytics session before logout
    this.analyticsService.endSession().subscribe();
    
    const wasAdmin = this.isAdmin;
    this.authService.logout();
    if (wasAdmin) {
      this.router.navigate(['/admin/login']);
    } else {
      this.router.navigate(['/login']);
    }
  }

  navigateToApiBrowser() {
    this.router.navigate(['/api-browser']);
  }

  openMovieDetail(movie: any, source?: string, position?: number) {
    // Set flags
    this.selectedMovieForDetail = movie;
    this.showMovieModal = true;
    this.similarMovies = [];
    this.loadingSimilar = true;
    
    // BRUTAL FIX: Manually show the modal using DOM
    setTimeout(() => {
      const modalElement = document.querySelector('.modal-backdrop') as HTMLElement;
      if (modalElement) {
        modalElement.style.display = 'flex';
        modalElement.style.visibility = 'visible';
        modalElement.style.opacity = '1';
      }
    }, 0);
    
    // Force Angular to update
    this.appRef.tick();
    this.cdr.detectChanges();
    
    // Track movie click
    this.analyticsService.trackMovieClick(this.username, movie.id, movie.title, movie.type);
    
    // ═══════════════════════════════════════════════════════════════════════
    // AI SELF-LEARNING: Track if this click came from AI recommendations
    // ✅ TEMPORARILY DISABLED - causing 500 errors
    // ═══════════════════════════════════════════════════════════════════════
    /* DISABLED FOR NOW
    if (source === 'ai_recommendations' && position !== undefined) {
      const genres = movie.listed_in ? movie.listed_in.split(',').map((g: string) => g.trim()) : [];
      const recommendationBatchId = `rec_${new Date().toISOString().split('T')[0]}_${this.username}_${Date.now()}`;
      
      this.analyticsService.trackRecommendationFeedback(
        this.username,
        recommendationBatchId,
        movie.id,
        movie.title,
        position + 1,  // Position is 0-indexed, convert to 1-indexed
        movie.similarity_score || 0,
        genres,
        this.favoriteGenres || [],
        this.recommendedMovies.length
      );
    }
    */
    
    // Simulate watch progress (since no video player exists yet)
    // Generate random watch percentage between 10-85% (started but not finished)
    // This creates Continue Watching data for testing
    const watchPercentage = Math.floor(Math.random() * 76) + 10; // 10-85%
    const watchDurationSeconds = Math.floor(Math.random() * 3600) + 600; // 10-60 minutes
    const totalDurationSeconds = 7200; // Assume 2-hour movie
    
    // Extract genres from movie
    const genres = movie.listed_in ? movie.listed_in.split(',').map((g: string) => g.trim()) : [];
    
    // Track as "watched" with progress (async)
    this.analyticsService.trackMovieWatch(
      this.username, 
      movie.id, 
      movie.title, 
      watchDurationSeconds, 
      watchPercentage, 
      totalDurationSeconds,
      genres
    );
    
    // Load similar movies in background (doesn't block modal opening)
    const genre = movie.listed_in ? movie.listed_in.split(',')[0].trim() : '';
    if (genre) {
      this.movieService.getMovies({
        page: 1,
        limit: 12,
        genre: genre,
        type: movie.type || ''
      }).subscribe({
        next: (res) => {
          // Filter out the current movie and take first 12
          this.similarMovies = (res && res.movies) 
            ? res.movies.filter((m: any) => m.id !== movie.id).slice(0, 12)
            : [];
          this.loadingSimilar = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.similarMovies = [];
          this.loadingSimilar = false;
          this.cdr.detectChanges();
        }
      });
    } else {
      this.loadingSimilar = false;
    }
  }

  closeMovieDetail() {
    this.selectedMovieForDetail = null;
    this.showMovieModal = false;
    
    // Also manually hide it
    const modalElement = document.querySelector('.modal-backdrop') as HTMLElement;
    if (modalElement) {
      modalElement.style.display = 'none';
    }
    
    this.cdr.detectChanges();
  }
  
  // Get or generate random watch progress for a movie
  getMovieProgress(movieId: string): number {
    // ✅ FIX: Check backend data first (continue watching)
    const continueMovie = this.continueWatchingMovies.find(m => m.movie_id === movieId || m.id === movieId);
    if (continueMovie && continueMovie.watching_percentage !== undefined && continueMovie.watching_percentage > 0) {
      return continueMovie.watching_percentage;
    }
    
    // ✅ FIX: Check if user manually set percentage
    if (this.movieWatchingPercentage[movieId] !== undefined && this.movieWatchingPercentage[movieId] > 0) {
      return this.movieWatchingPercentage[movieId];
    }
    
    // ✅ FIX: Default to 0 (don't show progress bar) instead of random
    return 0;
  }
  
  // Get user-editable watching percentage (from backend or default 0)
  getMovieWatchingPercentage(movieId: string): number {
    // ✅ PRIORITY 1: Check local edits first (most recent)
    if (this.movieWatchingPercentage[movieId] !== undefined) {
      return this.movieWatchingPercentage[movieId];
    }
    
    // ✅ PRIORITY 2: Check continue watching API data
    const continueMovie = this.continueWatchingMovies.find(m => m.movie_id === movieId || m.id === movieId);
    if (continueMovie && continueMovie.watching_percentage !== undefined) {
      // Cache in local state
      this.movieWatchingPercentage[movieId] = continueMovie.watching_percentage;
      return continueMovie.watching_percentage;
    }
    
    // ✅ DEFAULT: 0 (no progress bar)
    return 0;
  }
  
  // Handle watching percentage change
  onWatchingPercentageChange(movieId: string, event: any) {
    const value = parseInt(event.target.value);
    
    // Validate
    if (isNaN(value) || value < 0 || value > 100) {
      this.errorMessage = 'Le pourcentage doit être entre 0 et 100';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }
    
    // ✅ FIX: Update locally first for immediate UI feedback
    this.movieWatchingPercentage[movieId] = value;
    
    // ✅ FIX: Update in continue watching list if exists
    const continueMovieIndex = this.continueWatchingMovies.findIndex(m => m.movie_id === movieId || m.id === movieId);
    if (continueMovieIndex !== -1) {
      this.continueWatchingMovies[continueMovieIndex].watching_percentage = value;
    }
    
    // Save to backend
    this.analyticsService.updateWatchingPercentage(this.username, movieId, value).subscribe({
      next: (res) => {
        if (res.success) {
          console.log(`✅ Updated watching percentage for ${movieId} to ${value}%`);
          // ✅ FIX: Refresh continue watching to get updated data from backend
          this.loadContinueWatching();
          // Trigger change detection
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        console.error('Error updating watching percentage:', err);
        this.errorMessage = 'Erreur lors de la mise à jour';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }
  
  // Get progress bar color based on percentage
  getProgressColor(progress: number): string {
    if (progress < 25) return '#ef4444'; // Red
    if (progress < 50) return '#f59e0b'; // Orange
    if (progress < 75) return '#3b82f6'; // Blue
    return '#10b981'; // Green
  }

  // Favorites/Wishlist functions
  toggleFavorite(movieId: string) {
    if (!this.username) return;
    
    const wasFavorite = this.favorites.has(movieId);
    
    this.movieService.toggleFavorite(this.username, movieId).subscribe({
      next: (res) => {
        this.favorites = new Set(res.favorites || []);
        localStorage.setItem(`favorites_${this.username}`, JSON.stringify(Array.from(this.favorites)));
        
        // Track analytics
        const movie = this.movies.find(m => m.id === movieId);
        if (movie) {
          if (wasFavorite) {
            this.analyticsService.trackRemoveFromWatchlist(this.username, movieId, movie.title);
          } else {
            this.analyticsService.trackAddToWatchlist(this.username, movieId, movie.title);
          }
        }
        
        if (this.showFavoritesOnly) {
          this.applyFavoritesFilterLocally();
        } else {
          this.cdr.detectChanges();
        }
      },
      error: () => {
        // Fallback local toggle
        if (this.favorites.has(movieId)) {
          this.favorites.delete(movieId);
        } else {
          this.favorites.add(movieId);
        }
        localStorage.setItem(`favorites_${this.username}`, JSON.stringify(Array.from(this.favorites)));
        if (this.showFavoritesOnly) {
          this.applyFavoritesFilterLocally();
        }
      }
    });
  }

  toggleFavoritesFilter() {
    this.showFavoritesOnly = !this.showFavoritesOnly;
    if (this.showFavoritesOnly) {
      this.loadFavoriteMovies();
    } else {
      this.currentPage = 1;
      this.loadMovies();
    }
    this.cdr.detectChanges();
  }

  isFavorite(movieId: string): boolean {
    return this.favorites.has(movieId);
  }

  saveFavorites() {
    localStorage.setItem('favorites', JSON.stringify(Array.from(this.favorites)));
  }

  // Server already returns paged movies, just return filteredMovies
  getPaginatedMovies(): any[] {
    return this.filteredMovies;
  }

  // Get visible page numbers for pagination
  getPages(): number[] {
    const pages: number[] = [];
    const maxVisible = 7;
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  }

  // Pagination navigation — triggers new server request
  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadMovies();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  nextPage() {
    this.goToPage(this.currentPage + 1);
  }

  previousPage() {
    this.goToPage(this.currentPage - 1);
  }

  // Export to CSV
  exportToCSV() {
    const moviesToExport = this.getPaginatedMovies();
    
    if (moviesToExport.length === 0) {
      this.errorMessage = 'No movies to export!';
      return;
    }

    // CSV header
    const headers = ['Title', 'Type', 'Year', 'Director', 'Cast', 'Country', 'Rating', 'Duration', 'Genres', 'Description'];
    
    // CSV rows
    const rows = moviesToExport.map(m => [
      `"${m.title || ''}"`,
      m.type || '',
      m.release_year || '',
      `"${m.director || ''}"`,
      `"${m.cast || ''}"`,
      m.country || '',
      m.rating || '',
      m.duration || '',
      `"${m.listed_in || ''}"`,
      `"${(m.description || '').replace(/"/g, '""')}"` // Escape quotes
    ]);

    // Combine headers and rows
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');

    // Download CSV
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `movies_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    this.successMessage = `Exported ${moviesToExport.length} movies to CSV!`;
  }

  // Export to JSON
  exportToJSON() {
    const moviesToExport = this.getPaginatedMovies();
    
    if (moviesToExport.length === 0) {
      this.errorMessage = 'No movies to export!';
      return;
    }

    const jsonData = JSON.stringify(moviesToExport, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `movies_${new Date().getTime()}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    this.successMessage = `Exported ${moviesToExport.length} movies to JSON!`;
  }

  // ─── Search Dropdown Methods ────────────────────────────
  onSearchBlur() {
    // Delay hiding dropdown to allow click events on dropdown items
    setTimeout(() => {
      this.searchFocused = false;
      this.showAllGenres = false;
      this.cdr.detectChanges();
    }, 200);
  }

  getTopGenres(): string[] {
    // Return first 8 genres
    return this.genresList.slice(0, 8);
  }

  getRemainingGenres(): string[] {
    // Return remaining genres after first 8
    return this.genresList.slice(8);
  }

  selectGenreFromDropdown(genre: string, event?: Event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    console.log('🎭🎭🎭 GENRE SELECTED:', genre);
    console.log('🎭 Current state:', {
      searchFocused: this.searchFocused,
      selectedGenre: this.selectedGenre,
      activeView: this.activeView
    });
    
    // Close dropdown immediately
    this.searchFocused = false;
    this.showAllGenres = false;
    this.combinedSearchQuery = '';
    this.searchQuery = '';
    
    // Set genre and apply filter
    this.selectedGenre = genre;
    this.currentPage = 1;
    this.activeView = 'home'; // Ensure we're on home view
    
    console.log('🎭 After setting genre:', this.selectedGenre);
    
    // Force immediate UI update
    this.cdr.detectChanges();
    
    // Force immediate filter application
    this.loadMovies();
    
    // Scroll to top
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 100);
    
    console.log('🎭 Genre selection completed');
  }
  dislikeMovie(movie: any, event: Event): void {
    try {
      event.stopPropagation();
      event.preventDefault();
      
      console.log('dislikeMovie called with:', movie);
      
      // Get the correct movie ID - prioritize movie_id field
      const movieId = movie.movie_id || movie.id || movie._id;
      
      console.log('Extracted movieId:', movieId);
      
      if (!movieId) {
        console.error('No movie ID found:', movie);
        this.errorMessage = 'ID du film introuvable';
        setTimeout(() => this.errorMessage = '', 3000);
        return;
      }
      
      const isFromRecommendations = this.recommendedMovies.some((m: any) => (m.movie_id || m.id) === movieId);
      let position = null;
      if (isFromRecommendations) {
        position = this.recommendedMovies.findIndex((m: any) => (m.movie_id || m.id) === movieId) + 1;
      }
      const dislikeData = {
        username: this.username,
        movie_id: movieId,
        dislike_reason: 'not_interested',
        was_ai_recommendation: isFromRecommendations,
        recommendation_position: position
      };
      
      console.log('Sending dislike request:', dislikeData);
      
      this.analyticsService.dislikeMovie(dislikeData).subscribe(
        (response: any) => {
          console.log('Movie disliked successfully:', response);
          // Don't show success message - user sees movie disappear which is enough
          
          // Remove from all arrays using consistent ID matching
          this.recommendedMovies = this.recommendedMovies.filter((m: any) => (m.movie_id || m.id || m._id) !== movieId);
          this.trendingMovies = this.trendingMovies.filter((m: any) => (m.movie_id || m.id || m._id) !== movieId);
          this.continueWatchingMovies = this.continueWatchingMovies.filter((m: any) => (m.movie_id || m.id || m._id) !== movieId);
          this.filteredMovies = this.filteredMovies.filter((m: any) => (m.movie_id || m.id || m._id) !== movieId);
          
          // Close modal
          this.selectedMovieForDetail = null;
          
          this.cdr.detectChanges();
        },
        (error: any) => {
          console.error('Error disliking movie:', error);
          this.errorMessage = 'Erreur lors du dislike: ' + (error.error?.error || error.message || 'Unknown error');
          setTimeout(() => this.errorMessage = '', 5000);
        }
      );
    } catch (err) {
      console.error('Exception in dislikeMovie:', err);
      this.errorMessage = 'Erreur: ' + err;
      setTimeout(() => this.errorMessage = '', 5000);
    }
  }
}