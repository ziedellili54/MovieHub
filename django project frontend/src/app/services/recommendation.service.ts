/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 RECOMMENDATION SERVICE - AI-Powered Movie Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Connect frontend to TensorFlow AI recommendation backend
    
WHAT IT DOES:
    - Get personalized recommendations for users
    - Get similar movies (content-based)
    - Health check for recommendation system
    
BACKEND:
    Django REST API with TensorFlow Hub Universal Sentence Encoder v4
    Creates 512-dimensional embeddings for content matching
    
USAGE:
    constructor(private recommendationService: RecommendationService) {
      this.recommendationService.getRecommendations('john', 10).subscribe(res => {
        this.recommendations = res.recommendations;
      });
    }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RecommendationService {
  private apiUrl = 'http://localhost:8000/api/recommendations';

  constructor(private http: HttpClient) {}

  /**
   * Get personalized recommendations for a user
   * Uses AI to match user preferences with movie content
   * 
   * @param username - User's username
   * @param count - Number of recommendations (default: 10)
   * @param genre - Optional genre filter
   * @param type - Optional type filter ("Movie" or "TV Show")
   * @returns Observable with recommendations
   */
  getRecommendations(username: string, count: number = 10, genre?: string, type?: string): Observable<any> {
    let params = new HttpParams().set('count', count.toString());
    
    if (genre) {
      params = params.set('genre', genre);
    }
    if (type) {
      params = params.set('type', type);
    }
    
    return this.http.get<any>(`${this.apiUrl}/${username}/`, { params });
  }

  /**
   * Get movies similar to a specific movie
   * Uses content-based filtering (title, genres, description)
   * 
   * @param movieId - Movie ID
   * @param count - Number of similar movies (default: 6)
   * @returns Observable with similar movies
   */
  getSimilarMovies(movieId: string, count: number = 6): Observable<any> {
    const params = new HttpParams().set('count', count.toString());
    return this.http.get<any>(`${this.apiUrl}/similar/${movieId}/`, { params });
  }

  /**
   * Get trending/popular movies
   * Shows what's most watched/favorited across all users
   * 
   * @param count - Number of movies (default: 20)
   * @param type - Optional type filter ("Movie" or "TV Show")
   * @param username - Optional username to filter dislikes
   * @returns Observable with trending movies
   */
  getTrending(count: number = 20, type?: string, username?: string): Observable<any> {
    let params = new HttpParams().set('count', count.toString());
    
    if (type) {
      params = params.set('type', type);
    }
    
    if (username) {
      params = params.set('username', username);
    }
    
    return this.http.get<any>(`${this.apiUrl}/trending/`, { params });
  }

  /**
   * Check if recommendation system is healthy
   * Useful for displaying status in admin panel
   * 
   * @returns Observable with health status
   */
  healthCheck(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/health/`);
  }

  /**
   * Index all movies (Admin only)
   * Should be called after adding new movies
   * 
   * @returns Observable with indexing results
   */
  indexMovies(): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/index-movies/`, {});
  }

  /**
   * Get all personalized sections for a user (NEW)
   * Returns 10 sections: AI recommendations, top watched, top searched, etc.
   * All sections are sorted by user's preferred genres
   * 
   * @param username - User's username
   * @returns Observable with all 10 sections
   */
  getAllSections(username: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/sections/${username}/`);
  }

  /**
   * Force regenerate personalized sections (NEW)
   * Use after user changes preferences or significant activity
   * 
   * @param username - User's username
   * @returns Observable with success status
   */
  regenerateSections(username: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/sections/${username}/regenerate/`, {});
  }
}
