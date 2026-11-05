/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ANALYTICS SERVICE - User Behavior Tracking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Track and analyze user behavior for:
    - Personalized recommendations
    - Usage analytics dashboard
    - Understanding user preferences
    - Business insights (watch time, engagement)

WHAT IT TRACKS:
    - App sessions (open/close)
    - Searches (what users search for)
    - Movie interactions (clicks, plays, watches)
    - Favorites (likes/dislikes)
    - Watch time and completion rates
    - Device and browser information

BACKEND CONNECTIONS:
    - POST /api/analytics/session/start/ → StartSessionView
    - POST /api/analytics/session/end/ → EndSessionView
    - POST /api/analytics/track/ → TrackActivityView
    - GET /api/analytics/user/{username}/ → GetUserAnalyticsView
    - GET /api/analytics/all/ → GetAllUsersAnalyticsView

MONGODB STORAGE:
    - user_activities collection (analytics_models.py UserActivity)
    - user_preferences collection (analytics_models.py UserPreferences)
    - user_sessions collection (analytics_models.py UserSession)

USAGE IN COMPONENTS:
    constructor(private analytics: AnalyticsService, private auth: AuthService) {
      const username = this.auth.getUsername();
      this.analytics.trackAppOpen(username);
    }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'  // Singleton service
})
export class AnalyticsService {
  // ═══════════════════════════════════════════════════════════════════════
  // CONFIGURATION & STATE
  // ═══════════════════════════════════════════════════════════════════════
  private apiUrl = 'http://localhost:8000/api/analytics';
  // Backend analytics API base URL
  
  private sessionId: string | null = null;
  // Current user session ID (set when app opens)
  // Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  // Used to: Link all activities during this session
  
  private sessionStart: Date | null = null;
  // When current session started (currently unused but useful for future)

  constructor(private http: HttpClient) {}

  // Start a new session
  startSession(username: string): Observable<any> {
    const deviceInfo = this.getDeviceInfo();
    return this.http.post<any>(`${this.apiUrl}/session/start/`, {
      username,
      ...deviceInfo
    });
  }

  // End current session
  endSession(): Observable<any> {
    if (!this.sessionId) {
      return new Observable(observer => observer.next({ success: true }));
    }
    return this.http.post<any>(`${this.apiUrl}/session/end/`, {
      session_id: this.sessionId
    });
  }

  // Track any activity
  trackActivity(data: {
    username: string;
    activity_type: string;
    movie_id?: string;
    movie_title?: string;
    movie_type?: string;
    search_query?: string;
    search_results_count?: number;
    watch_duration_seconds?: number;
    watch_percentage?: number;
    total_duration_seconds?: number;
    category?: string;
    genres?: string[];
    time_spent_seconds?: number;
    metadata?: any;
  }): Observable<any> {
    const deviceInfo = this.getDeviceInfo();
    return this.http.post<any>(`${this.apiUrl}/track/`, {
      ...data,
      session_id: this.sessionId,
      ...deviceInfo
    });
  }

  // Convenience methods for specific activities
  
  trackAppOpen(username: string): void {
    this.startSession(username).subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.sessionStart = new Date();
      },
      error: (err) => console.error('Error starting session:', err)
    });
  }

  trackSearch(username: string, query: string, resultsCount: number): void {
    this.trackActivity({
      username,
      activity_type: 'search',
      search_query: query,
      search_results_count: resultsCount
    }).subscribe();
  }

  trackMovieClick(username: string, movieId: string, movieTitle: string, movieType: string): void {
    this.trackActivity({
      username,
      activity_type: 'movie_click',
      movie_id: movieId,
      movie_title: movieTitle,
      movie_type: movieType
    }).subscribe();
  }

  trackMoviePlay(username: string, movieId: string, movieTitle: string): void {
    this.trackActivity({
      username,
      activity_type: 'movie_play',
      movie_id: movieId,
      movie_title: movieTitle
    }).subscribe();
  }

  trackMovieWatch(username: string, movieId: string, movieTitle: string, watchDuration: number, watchPercentage: number, totalDuration: number, genres?: string[]): void {
    this.trackActivity({
      username,
      activity_type: 'movie_watch',
      movie_id: movieId,
      movie_title: movieTitle,
      watch_duration_seconds: watchDuration,
      watch_percentage: watchPercentage,
      total_duration_seconds: totalDuration,
      genres: genres || []
    }).subscribe();
  }

  trackMovieFinish(username: string, movieId: string, movieTitle: string): void {
    this.trackActivity({
      username,
      activity_type: 'movie_finish',
      movie_id: movieId,
      movie_title: movieTitle
    }).subscribe();
  }

  trackAddToWatchlist(username: string, movieId: string, movieTitle: string): void {
    this.trackActivity({
      username,
      activity_type: 'add_watchlist',
      movie_id: movieId,
      movie_title: movieTitle
    }).subscribe();
  }

  trackRemoveFromWatchlist(username: string, movieId: string, movieTitle: string): void {
    this.trackActivity({
      username,
      activity_type: 'remove_watchlist',
      movie_id: movieId,
      movie_title: movieTitle
    }).subscribe();
  }

  trackLike(username: string, movieId: string, movieTitle: string): void {
    this.trackActivity({
      username,
      activity_type: 'like',
      movie_id: movieId,
      movie_title: movieTitle
    }).subscribe();
  }

  trackDislike(username: string, movieId: string, movieTitle: string): void {
    this.trackActivity({
      username,
      activity_type: 'dislike',
      movie_id: movieId,
      movie_title: movieTitle
    }).subscribe();
  }

  trackPurchase(username: string, movieId: string, movieTitle: string, amount?: number): void {
    this.trackActivity({
      username,
      activity_type: 'purchase',
      movie_id: movieId,
      movie_title: movieTitle,
      metadata: { amount }
    }).subscribe();
  }

  trackBrowse(username: string, category: string, timeSpent: number): void {
    this.trackActivity({
      username,
      activity_type: 'browse',
      category,
      time_spent_seconds: timeSpent
    }).subscribe();
  }

  trackCategoryVisit(username: string, category: string, genres: string[]): void {
    this.trackActivity({
      username,
      activity_type: 'category_visit',
      category,
      genres
    }).subscribe();
  }

  // ═══════════════════════════════════════════════════════════════════════
  // AI SELF-LEARNING: Track Recommendation Feedback
  // ═══════════════════════════════════════════════════════════════════════
  trackRecommendationFeedback(
    username: string,
    recommendationBatchId: string,
    recommendedMovieId: string,
    recommendedMovieTitle: string,
    recommendationPosition: number,
    similarityScore: number,
    recommendedGenres: string[],
    userFavoriteGenres: string[],
    totalRecommendations: number
  ): void {
    this.http.post<any>('http://localhost:8000/api/analytics/recommendation-feedback/', {
      username,
      recommendation_batch_id: recommendationBatchId,
      recommended_movie_id: recommendedMovieId,
      recommended_movie_title: recommendedMovieTitle,
      recommendation_position: recommendationPosition,
      similarity_score: similarityScore,
      recommended_genres: recommendedGenres,
      user_favorite_genres_at_time: userFavoriteGenres,
      total_recommendations_in_batch: totalRecommendations,
      recommended_at: new Date().toISOString()
    }).subscribe({
      next: (res) => {
        console.log('✅ AI Feedback tracked:', res);
        if (res.feedback_category === 'excellent' || res.feedback_category === 'good') {
          console.log('🎯 AI is learning your preferences well!');
        } else if (res.feedback_category === 'bad' || res.feedback_category === 'very_bad') {
          console.log('📊 AI will improve based on this feedback');
        }
      },
      error: (err) => console.error('Error tracking recommendation feedback:', err)
    });
  }

  // Get user analytics
  getUserAnalytics(username: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/user/${username}/`);
  }

  // Get all users analytics (admin)
  getAllUsersAnalytics(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/all/`);
  }

  // Get user's watch history with percentages (for Continue Watching)
  getUserMoviePercentages(username: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/user/${username}/movies/`);
  }

  // Get device information
  private getDeviceInfo() {
    const ua = navigator.userAgent;
    
    // Detect device type
    let deviceType = 'desktop';
    if (/mobile/i.test(ua)) {
      deviceType = 'mobile';
    } else if (/tablet|ipad/i.test(ua)) {
      deviceType = 'tablet';
    }

    // Detect browser
    let browser = 'unknown';
    if (ua.indexOf('Firefox') > -1) {
      browser = 'Firefox';
    } else if (ua.indexOf('Chrome') > -1) {
      browser = 'Chrome';
    } else if (ua.indexOf('Safari') > -1) {
      browser = 'Safari';
    } else if (ua.indexOf('Edge') > -1) {
      browser = 'Edge';
    }

    // Detect OS
    let os = 'unknown';
    if (ua.indexOf('Win') > -1) {
      os = 'Windows';
    } else if (ua.indexOf('Mac') > -1) {
      os = 'macOS';
    } else if (ua.indexOf('Linux') > -1) {
      os = 'Linux';
    } else if (ua.indexOf('Android') > -1) {
      os = 'Android';
    } else if (ua.indexOf('iOS') > -1) {
      os = 'iOS';
    }

    // Get country (placeholder - in production use geolocation API)
    const country = 'Unknown';  // You can use a geolocation service

    return {
      device_type: deviceType,
      browser: browser,
      os: os,
      country: country,
      ip_address: ''  // Backend can capture this
    };
  }

  // Store session ID
  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
  
  /**
   * Update user-editable watching percentage for a movie
   */
  updateWatchingPercentage(username: string, movieId: string, watchingPercentage: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/update-watching-percentage/`, {
      username,
      movie_id: movieId,
      watching_percentage: watchingPercentage
    });
  }
  
  /**
   * Get Continue Watching list (movies with user-set watching_percentage > 0)
   */
  getContinueWatching(username: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/continue-watching/${username}/`);
  }

  dislikeMovie(data: any): Observable<any> {
    // Dislike endpoint is at /api/dislikes/, not /api/analytics/dislikes/
    return this.http.post('http://localhost:8000/api/dislikes/', data);
  }
}