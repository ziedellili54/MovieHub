"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PERSONALIZED SECTIONS ENGINE - Generate Dashboard Sections for Each User
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Generate personalized dashboard sections that are:
    - Same content for all users (global data)
    - Sorted by each user's genre preferences (personalized)
    - Saved in MongoDB for fast loading
    - Updated when user preferences change (not recreated)

SECTIONS GENERATED:
    1. AI Recommendations (20 movies)
    2. Top Watched Movies (all-time)
    3. Top Watched Series (all-time)
    4. Top Searched Movies
    5. Top Searched Series
    6. Top 10 Movies
    7. Top 10 Series
    8. Top 20 Favorites (all users)
    9. Newly Added Movies
    10. Newly Added Series

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from typing import List, Dict, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from accounts.analytics_models import (
    UserPersonalizedSections,
    UserActivity,
    UserPreferences,
    MovieWatchHistory,
    MovieDislike
)
from accounts.models import Favorite, User
from movies.models import Movie, TVShow


class PersonalizedSectionsEngine:
    """
    Generate and update personalized dashboard sections for users
    """
    
    def __init__(self):
        self.SECTION_SIZE = 20  # Default section size
        
    # ═══════════════════════════════════════════════════════════════════════
    # MAIN FUNCTION: Generate or Update All Sections
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_sections_for_user(self, username: str, force_regenerate: bool = False) -> Dict:
        """
        Generate or update all personalized sections for a user
        
        Args:
            username: Username
            force_regenerate: Force regeneration even if not stale
            
        Returns:
            Dict with all sections
        """
        try:
            print(f"\n{'='*80}")
            print(f"Generating personalized sections for: {username}")
            print(f"{'='*80}")
            
            # Check if sections exist and are fresh
            existing = UserPersonalizedSections.objects(username=username).first()
            
            if existing and not force_regenerate and not existing.is_stale(hours=24):
                print(f"Using cached sections (last updated: {existing.last_updated})")
                return self._sections_to_dict(existing)
            
            # Get user's preferred genres
            user_genres = self._get_user_preferred_genres(username)
            print(f"User preferred genres: {user_genres[:5]}")
            
            # Get user's disliked movies to filter them out
            disliked_ids = self._get_disliked_movie_ids(username)
            print(f"Filtering {len(disliked_ids)} disliked movies")
            
            # Generate each section
            sections_data = {}
            
            # 1. AI Recommendations (from recommendation engine)
            print("\nSection 1: AI Recommendations...")
            sections_data['ai_recommendations'] = self._get_ai_recommendations(username, user_genres, disliked_ids)
            
            # 2. Top Watched Movies
            print("Section 2: Top Watched Movies...")
            sections_data['top_watched_movies'] = self._get_top_watched_movies(user_genres, disliked_ids)
            
            # 3. Top Watched Series
            print("Section 3: Top Watched Series...")
            sections_data['top_watched_series'] = self._get_top_watched_series(user_genres, disliked_ids)
            
            # 4. Top Searched Movies
            print("Section 4: Top Searched Movies...")
            sections_data['top_searched_movies'] = self._get_top_searched_movies(user_genres, disliked_ids)
            
            # 5. Top Searched Series
            print("Section 5: Top Searched Series...")
            sections_data['top_searched_series'] = self._get_top_searched_series(user_genres, disliked_ids)
            
            # 6. Top 10 Movies
            print("Section 6: Top 10 Movies...")
            sections_data['top_10_movies'] = self._get_top_10_movies(user_genres, disliked_ids)
            
            # 7. Top 10 Series
            print("Section 7: Top 10 Series...")
            sections_data['top_10_series'] = self._get_top_10_series(user_genres, disliked_ids)
            
            # 8. Top 20 Favorites
            print("Section 8: Top 20 Favorites...")
            sections_data['top_20_favorites'] = self._get_top_favorites(user_genres, disliked_ids, count=20)
            
            # 9. Newly Added Movies
            print("Section 9: Newly Added Movies...")
            sections_data['newly_added_movies'] = self._get_newly_added_movies(user_genres, disliked_ids)
            
            # 10. Newly Added Series
            print("Section 10: Newly Added Series...")
            sections_data['newly_added_series'] = self._get_newly_added_series(user_genres, disliked_ids)
            
            # Save or update in MongoDB
            if existing:
                print(f"\nUpdating existing sections...")
                self._update_sections(existing, sections_data, user_genres)
            else:
                print(f"\nCreating new sections...")
                self._create_sections(username, sections_data, user_genres)
            
            print(f"{'='*80}")
            print(f"Sections generated successfully for {username}")
            print(f"{'='*80}\n")
            
            return sections_data
            
        except Exception as e:
            print(f"Error generating sections: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _calculate_genre_weights(self, username: str) -> dict:
        """
        Calculate genre weights for a user (returns raw weight dictionary)
        This is used to determine dynamic quotas
        """
        from collections import Counter
        genre_weights = Counter()
        
        # Recent completed (300 pts each)
        try:
            recent_completed = MovieWatchHistory.objects(
                username=username,
                watching_percentage__gte=85
            ).order_by('-last_watched')[:5]
            
            for watch in recent_completed:
                if watch.genres:
                    for genre in watch.genres:
                        if genre and genre.strip():
                            genre_weights[genre.strip()] += 300
        except:
            pass
        
        # Continue Watching (100 pts each)
        try:
            continue_watching = MovieWatchHistory.objects(
                username=username,
                watching_percentage__gt=5,
                watching_percentage__lt=85
            ).order_by('-last_watched')[:10]
            
            for watch in continue_watching:
                if watch.genres:
                    for genre in watch.genres:
                        if genre and genre.strip():
                            genre_weights[genre.strip()] += 100
        except:
            pass
        
        # Favorites (80 pts)
        try:
            favorites = Favorite.objects(username=username)[:20]
            for fav in favorites:
                try:
                    movie = None
                    try:
                        movie = Movie.objects.get(id=fav.movie_id)
                    except:
                        movie = TVShow.objects.get(id=fav.movie_id)
                    
                    if movie and hasattr(movie, 'listed_in') and movie.listed_in:
                        genres = [g.strip() for g in movie.listed_in.split(',')]
                        for idx, genre in enumerate(genres[:3]):
                            if genre:
                                weight = 80 if idx == 0 else 40
                                genre_weights[genre] += weight
                except:
                    continue
        except:
            pass
        
        # Manual preferences (150 pts)
        try:
            prefs = UserPreferences.objects.get(username=username)
            if prefs.favorite_genres:
                for idx, genre in enumerate(prefs.favorite_genres[:5]):
                    if genre and genre.strip():
                        boost = 150 if idx < 2 else 75
                        genre_weights[genre.strip()] += boost
        except:
            pass
        
        return dict(genre_weights)

    def _get_user_preferred_genres(self, username: str) -> list:
        """
        Get user's preferred genres - SMART AI that AUTOMATICALLY tracks from database
        
        🎯 NEW BEHAVIOR: RECENT activity is KING!
        
        Priority Sources (automatic detection):
        1. RECENTLY COMPLETED (last 5 movies at 85%+) - ULTRA HIGH WEIGHT (300 pts)
           → If you watch 3 Comedy movies, Comedy appears IMMEDIATELY!
        2. Continue Watching (currently watching) - HIGH weight (100 pts)
        3. Favorites (what you liked) - MEDIUM weight (80 pts)  
        4. Old Completed (older than last 5) - LOW weight (30 pts)
        5. Manual Selection (UserPreferences) - VERY HIGH weight (150 pts)
        
        ✅ FIX: Recent behavior (last 5 completed) gets 3x weight of Continue Watching!
        This means if you complete 3 Comedy movies, Comedy becomes your #1 genre instantly!
        """
        from collections import Counter
        genre_weights = Counter()
        
        # ══════════════════════════════════════════════════════════════════
        # SOURCE 1: RECENTLY COMPLETED (ULTRA HIGHEST PRIORITY - shows current mood!)
        # ✅ NEW: Last 5 completed movies get MASSIVE weight (300 pts each!)
        # This means if you watch 3 Comedy movies, Comedy becomes #1 genre instantly!
        # ══════════════════════════════════════════════════════════════════
        try:
            recent_completed = MovieWatchHistory.objects(
                username=username,
                watching_percentage__gte=85  # Completed (watched till end)
            ).order_by('-last_watched')[:5]  # Only last 5!
            
            recent_count = len(list(recent_completed))
            
            for watch in recent_completed:
                # ULTRA HIGH weight for RECENTLY completed
                # 300 pts = 3x more than Continue Watching!
                weight = 300
                
                if watch.genres:
                    for genre in watch.genres:
                        if genre and genre.strip():
                            genre_weights[genre.strip()] += weight
            
            if recent_count > 0:
                print(f"   🔥 RECENT Completed: {recent_count} movies (ULTRA HIGH priority - 300 pts each)")
        except Exception as e:
            print(f"   ⚠️  Recent Completed: {e}")
        
        # ══════════════════════════════════════════════════════════════════
        # SOURCE 2: CONTINUE WATCHING (HIGH PRIORITY - currently watching)
        # ══════════════════════════════════════════════════════════════════
        try:
            continue_watching = MovieWatchHistory.objects(
                username=username,
                watching_percentage__gt=5,  # Started watching
                watching_percentage__lt=85   # Not finished yet
            ).order_by('-last_watched')[:10]
            
            for watch in continue_watching:
                # High weight for what user is CURRENTLY watching
                weight = 100
                
                if watch.genres:
                    for genre in watch.genres:
                        if genre and genre.strip():
                            genre_weights[genre.strip()] += weight
            
            if continue_watching:
                print(f"   📺 Continue Watching: {len(list(continue_watching))} items (HIGH priority)")
        except Exception as e:
            print(f"   ⚠️  Continue Watching: {e}")
        
        # ══════════════════════════════════════════════════════════════════
        # SOURCE 3: FAVORITES (MEDIUM PRIORITY - explicit preferences)
        # ══════════════════════════════════════════════════════════════════
        try:
            favorites = Favorite.objects(username=username)[:20]
            
            for fav in favorites:
                try:
                    movie = None
                    try:
                        movie = Movie.objects.get(id=fav.movie_id)
                    except:
                        movie = TVShow.objects.get(id=fav.movie_id)
                    
                    if movie and hasattr(movie, 'listed_in') and movie.listed_in:
                        genres = [g.strip() for g in movie.listed_in.split(',')]
                        
                        # Medium weight for favorites
                        for idx, genre in enumerate(genres[:3]):
                            if genre:
                                # Primary genre gets more weight
                                weight = 80 if idx == 0 else 40
                                genre_weights[genre] += weight
                except:
                    continue
            
            if favorites:
                print(f"   ⭐ Favorites: {len(list(favorites))} items (MEDIUM priority)")
        except Exception as e:
            print(f"   ⚠️  Favorites: {e}")
        
        # ══════════════════════════════════════════════════════════════════
        # SOURCE 4: OLD COMPLETED WATCH HISTORY (LOW PRIORITY - past behavior)
        # ✅ Changed: Skip the last 5 (already counted above), only older ones
        # ══════════════════════════════════════════════════════════════════
        try:
            old_completed = MovieWatchHistory.objects(
                username=username,
                watching_percentage__gte=85  # Finished watching
            ).order_by('-last_watched')[5:20]  # Skip first 5, get next 15
            
            for watch in old_completed:
                weight = 30  # Low priority (old behavior)
                
                if watch.genres:
                    for idx, genre in enumerate(watch.genres[:3]):
                        if genre and genre.strip():
                            # Primary genre gets more weight
                            w = weight if idx == 0 else weight // 2
                            genre_weights[genre.strip()] += w
            
            if old_completed:
                print(f"   📜 Old Completed: {len(list(old_completed))} items (LOW priority - past)")
        except Exception as e:
            print(f"   ⚠️  Old Completed: {e}")
        
        # ══════════════════════════════════════════════════════════════════
        # SOURCE 5: USER ACTIVITIES (VERY LOW PRIORITY - exploratory behavior)
        # ══════════════════════════════════════════════════════════════════
        try:
            activities = UserActivity.objects(username=username).order_by('-timestamp')[:20]
            
            for activity in activities:
                weight = 10  # Very low priority (they might just be browsing)
                
                if activity.genres:
                    for genre in activity.genres:
                        if genre and genre.strip():
                            genre_weights[genre.strip()] += weight
            
            if activities:
                print(f"   🖱️  Activities: {len(list(activities))} items (VERY LOW priority)")
        except Exception as e:
            print(f"   ⚠️  Activities: {e}")
        
        # ══════════════════════════════════════════════════════════════════
        # SOURCE 6: MANUAL SELECTION (VERY HIGH PRIORITY - user explicitly chose!)
        # ✅ Manual preferences ADD to automatic detection (not replace!)
        # ══════════════════════════════════════════════════════════════════
        try:
            prefs = UserPreferences.objects.get(username=username)
            if prefs.favorite_genres:
                # ✅ Give VERY HIGH weight to manually selected genres
                manual_weight = 150  # Between Continue Watching (100) and Recent Completed (300)
                
                for idx, genre in enumerate(prefs.favorite_genres[:5]):
                    if genre and genre.strip():
                        # First 2 manual selections get extra boost
                        boost = manual_weight if idx < 2 else (manual_weight // 2)
                        genre_weights[genre.strip()] += boost
                
                print(f"   📝 Manual Selection: {prefs.favorite_genres[:5]} (VERY HIGH priority - {manual_weight} pts)")
        except:
            pass
        
        # ══════════════════════════════════════════════════════════════════
        # RETURN TOP 5 GENRES BY COMBINED AUTOMATIC + MANUAL WEIGHT
        # ✅ FIX: Now includes BOTH automatic detection AND manual choices!
        # ══════════════════════════════════════════════════════════════════
        if genre_weights:
            top_genres = [genre for genre, weight in genre_weights.most_common(5)]
            
            print(f"   📊 AI Detected Genres (AUTOMATIC from database):")
            for genre, weight in genre_weights.most_common(5):
                print(f"      {genre}: {weight} pts")
            
            return top_genres
        
        # No data at all - return empty (new user with no activity)
        print(f"   ℹ️  New user - no activity detected yet")
        return []

    def _get_disliked_movie_ids(self, username: str) -> set:
        """Get set of disliked movie IDs"""
        try:
            dislikes = MovieDislike.objects(username=username)
            return set([str(d.movie_id) for d in dislikes])
        except Exception:
            return set()

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1: AI Recommendations
    # ═══════════════════════════════════════════════════════════════════════

    def _get_ai_recommendations(self, username: str, user_genres: list, disliked_ids: set) -> dict:
        """
        FAST AI: Get recommendations WITHOUT TensorFlow (instant load)
        Netflix-style: Balanced mix from ALL user genres
        
        ✅ FIX: Now receives AI-DETECTED genres as parameter
        ✅ FIX: FORCED INTERLEAVING to guarantee genre mix
        """
        print(f"   🚀 FAST MODE: Smart AI without TensorFlow")
        
        try:
            if not user_genres:
                # No activity - return popular movies
                popular = list(Movie.objects(imdb_rating__gte=7.5).order_by('-imdb_rating')[:20])
                movie_ids = [str(m.id) for m in popular]
                metadata = {mid: {'score': 100-(i*2), 'reason': 'Popular', 'position': i+1} for i, mid in enumerate(movie_ids)}
                return {'ids': movie_ids, 'metadata': metadata}
                movie_ids = [str(m.id) for m in popular]
                metadata = {mid: {'score': 100-(i*2), 'reason': 'Popular', 'position': i+1} for i, mid in enumerate(movie_ids)}
                return {'ids': movie_ids, 'metadata': metadata}
            
            # ✅ SMART DYNAMIC QUOTAS based on genre strength!
            # Calculate quotas based on actual genre weights
            genre_weights_dict = self._calculate_genre_weights(username)
            
            # Calculate total weight for percentage calculation
            genre_weights_for_quotas = [(g, genre_weights_dict.get(g, 0)) for g in user_genres]
            total_weight = sum(w for _, w in genre_weights_for_quotas)
            
            if total_weight == 0:
                # Fallback: if no weights, use equal distribution for top 5
                num_genres = min(len(user_genres), 5)
                quotas = [20 // num_genres] * num_genres
            else:
                # Dynamic quotas based on actual strength
                quotas = []
                for genre, weight in genre_weights_for_quotas:
                    percentage = weight / total_weight
                    quota = max(1, round(20 * percentage))  # At least 1 movie
                    quotas.append(quota)
                
                # Adjust to exactly 20 movies
                while sum(quotas) > 20:
                    max_idx = quotas.index(max(quotas))
                    quotas[max_idx] -= 1
                
                while sum(quotas) < 20:
                    max_idx = quotas.index(max(quotas))
                    quotas[max_idx] += 1
            
            # ✅ Get movies for each genre with dynamic quotas
            genre_buckets = []
            
            for idx, genre in enumerate(user_genres):
                if idx >= len(quotas):
                    break
                
                quota = quotas[idx]
                if quota == 0:
                    continue  # Skip weak genres
                # Get movies for this specific genre
                genre_movies = list(Movie.objects(listed_in__icontains=genre).order_by('-imdb_rating'))
                
                # Filter out disliked and duplicates
                genre_movies = [m for m in genre_movies if str(m.id) not in disliked_ids]
                
                # Get quota for this genre position
                quota = quotas[idx] if idx < len(quotas) else 1
                
                # Take top N from this genre
                top_n = genre_movies[:quota]
                genre_buckets.append((genre, top_n))
                
                weight = genre_weights_dict.get(genre, 0)
                pct = (quota / 20) * 100
                print(f"   📊 Genre {idx+1} '{genre}': {len(top_n)}/{quota} movies ({pct:.0f}%) [weight: {weight} pts]")
            
            # ✅ INTERLEAVE movies from each genre bucket
            # Pattern: [Crime, Adventure, Crime, Adventure, Crime, Adventure, ...]
            # This GUARANTEES both genres appear, not just the highest-rated one
            recommendations = []
            max_len = max((len(movies) for _, movies in genre_buckets), default=0)
            
            for i in range(max_len):
                for genre, movies in genre_buckets:
                    if i < len(movies):
                        recommendations.append(movies[i])
                    if len(recommendations) >= 20:
                        break
                if len(recommendations) >= 20:
                    break
            
            # Convert to IDs and metadata
            movie_ids = [str(m.id) for m in recommendations[:20]]
            metadata = {mid: {'score': 100-(i*2), 'reason': 'For you', 'position': i+1} for i, mid in enumerate(movie_ids)}
            
            # Show distribution
            genre_dist = {}
            for m in recommendations[:20]:
                m_genres = [g.strip() for g in m.listed_in.split(',')] if hasattr(m, 'listed_in') and m.listed_in else []
                for ug in user_genres:  # ✅ Check ALL user genres, not just first 3
                    if any(ug.lower() in mg.lower() for mg in m_genres):
                        genre_dist[ug] = genre_dist.get(ug, 0) + 1
                        break
            
            print(f"   ✅ {len(movie_ids)} recommendations:")
            for genre, count in genre_dist.items():
                pct = (count / len(movie_ids)) * 100 if movie_ids else 0
                print(f"      - {genre}: {count}/{len(movie_ids)} ({pct:.0f}%)")
            
            return {'ids': movie_ids, 'metadata': metadata}
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return {'ids': [], 'metadata': {}}


    def _get_trending(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """
        TRENDING: Show NEWEST releases (2023-2026) sorted by IMDB rating
        This is what NETFLIX shows in "Trending Now" - recent + popular
        """
        try:
            # Get movies from 2023-2026 (NEWEST releases)
            recent_movies = list(Movie.objects(release_year__gte=2023).order_by('-release_year'))
            recent_series = list(TVShow.objects(release_year__gte=2023).order_by('-release_year'))
            
            all_content = recent_movies + recent_series
            
            # Filter dislikes
            all_content = [c for c in all_content if str(c.id) not in disliked_ids]
            
            # Sort by IMDB rating (high to low)
            sorted_content = self._sort_by_user_genres(all_content, user_genres, disliked_ids)
            
            content_ids = [str(c.id) for c in sorted_content[:self.SECTION_SIZE]]
            scores = {cid: 100 for cid in content_ids}
            
            print(f"   Got {len(content_ids)} trending items (2023-2026)")
            return {'ids': content_ids, 'scores': scores}
        except Exception as e:
            print(f"   Error getting trending: {e}")
            return {'ids': [], 'scores': {}}
    
    def _get_top_watched_movies(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get top watched movies - FAMOUS high-rated movies with user activity"""
        return self._get_top_watched('Movie', user_genres, disliked_ids)
    
    def _get_top_watched_series(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get top watched series - FAMOUS high-rated series with user activity"""
        return self._get_top_watched('TV Show', user_genres, disliked_ids)
    
    def _get_trending_score(self, movie_id: str, days: int = 7) -> int:
        """
        Calculate trending score based on recent global user activity
        
        ✅ NEW: Movies that many users watched/favorited recently get higher ranking
        
        Args:
            movie_id: Movie ID to check
            days: Look back period (default 7 days)
        
        Returns:
            Trending score (higher = more popular recently)
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        score = 0
        
        try:
            # Count recent watches (users who watched this in last N days)
            recent_watches = MovieWatchHistory.objects(
                movie_id=movie_id,
                last_watched__gte=cutoff_date.strftime("%Y-%m-%d")
            ).count()
            
            score += recent_watches * 10  # Each recent watch = 10 pts
            
        except Exception as e:
            pass
        
        try:
            # Count recent favorites (users who favorited this in last N days)
            # (Favorites don't have timestamp, so we count all)
            recent_favs = Favorite.objects(movie_id=movie_id).count()
            
            score += recent_favs * 20  # Each favorite = 20 pts (stronger signal)
            
        except Exception as e:
            pass
        
        return score
    
    def _get_top_watched(self, content_type: str, user_genres: List[str], disliked_ids: set) -> Dict:
        """
        GLOBALLY FAMOUS + User Activity + TRENDING
        
        ✅ NEW: Now includes trending score!
        If "Joker" was watched by 1000 users this week → ranks higher!
        """
        try:
            Model = Movie if content_type == 'Movie' else TVShow
            
            # Get ALL high-rated content from database (7.5+ rating)
            high_rated = list(Model.objects(imdb_rating__gte=7.5).order_by('-imdb_rating'))
            
            print(f"   Searching {len(high_rated)} high-rated {content_type}s from database")
            
            # ✅ NEW: Calculate trending scores for each movie
            trending_scores = {}
            for item in high_rated[:100]:  # Check top 100 for performance
                trending_scores[str(item.id)] = self._get_trending_score(str(item.id))
            
            # Filter dislikes
            content_list = [item for item in high_rated if str(item.id) not in disliked_ids]
            
            # Sort by user preferences using Smart AI (includes trending bonus)
            sorted_content = self._sort_by_user_genres_with_trending(
                content_list, user_genres, disliked_ids, trending_scores
            )
            
            movie_ids = [str(m.id) for m in sorted_content[:self.SECTION_SIZE]]
            scores = {mid: 100 for mid in movie_ids}
            
            # Log top trending
            if trending_scores:
                top_trending = sorted(trending_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                if any(score > 0 for _, score in top_trending):
                    print(f"   🔥 Top trending: {[(mid[:8], score) for mid, score in top_trending if score > 0]}")
            
            print(f"   Selected {len(movie_ids)} {content_type}s (sorted by taste + trending)")
            return {'ids': movie_ids, 'scores': scores}
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return {'ids': [], 'scores': {}}
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 4-5: Top Searched Movies/Series
    # ═══════════════════════════════════════════════════════════════════════
    
    def _get_top_searched_movies(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get top searched movies"""
        return self._get_top_searched('Movie', user_genres, disliked_ids)
    
    def _get_top_searched_series(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get top searched series"""
        return self._get_top_searched('TV Show', user_genres, disliked_ids)
    
    def _get_top_searched(self, content_type: str, user_genres: List[str], disliked_ids: set) -> Dict:
        """
        GLOBALLY MOST SEARCHED - Search ALL popular content with high votes
        """
        try:
            Model = Movie if content_type == 'Movie' else TVShow
            
            # Get ALL content with vote counts (popularity indicator)
            popular_content = list(Model.objects(imdb_votes__gte=50000).order_by('-imdb_votes', '-imdb_rating'))
            
            print(f"   Searching {len(popular_content)} popular {content_type}s from database")
            
            # Filter dislikes
            popular_content = [c for c in popular_content if str(c.id) not in disliked_ids]
            
            # Sort by user preferences using Smart AI
            sorted_content = self._sort_by_user_genres(popular_content, user_genres, disliked_ids)
            
            movie_ids = [str(m.id) for m in sorted_content[:self.SECTION_SIZE]]
            scores = {mid: i+1 for i, mid in enumerate(movie_ids)}
            
            print(f"   Selected {len(movie_ids)} {content_type}s sorted by user taste")
            return {'ids': movie_ids, 'scores': scores}
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return {'ids': [], 'scores': {}}
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 6-7: Top 10 Movies/Series
    # ═══════════════════════════════════════════════════════════════════════
    
    def _get_top_10_movies(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get top 10 movies (best rated/most popular)"""
        return self._get_top_10('Movie', user_genres, disliked_ids)
    
    def _get_top_10_series(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get top 10 series - DIRECTLY return famous high-rated series"""
        return self._get_top_10('TV Show', user_genres, disliked_ids)
    
    def _get_top_10(self, content_type: str, user_genres: List[str], disliked_ids: set) -> Dict:
        """
        NETFLIX LOGIC: Return FAMOUS high-rated content DIRECTLY
        No complex scoring - just return the best movies/series everyone knows
        """
        try:
            Model = Movie if content_type == 'Movie' else TVShow
            
            # DIRECTLY fetch famous titles from database
            FAMOUS_MOVIES = [
                'The Shawshank Redemption', 'The Godfather', 'The Dark Knight',
                'Pulp Fiction', 'Forrest Gump', 'Fight Club', 'The Matrix',
                'Interstellar', 'Inception', 'Parasite', 'Joker', 'Gladiator'
            ]
            FAMOUS_SERIES = [
                'Breaking Bad', 'Game of Thrones', 'The Sopranos', 'The Wire',
                'Stranger Things', 'The Crown', 'Sherlock', 'Chernobyl',
                'Friends', 'The Office', 'Supernatural', 'Sacred Games'
            ]
            
            famous_list = FAMOUS_SERIES if content_type == 'TV Show' else FAMOUS_MOVIES
            
            # Fetch these specific titles from database
            found_content = []
            for title in famous_list:
                try:
                    item = Model.objects(title=title).first()
                    if item and str(item.id) not in disliked_ids:
                        found_content.append(item)
                except:
                    continue
            
            # If we found famous content, return it
            if len(found_content) >= 5:
                movie_ids = [str(m.id) for m in found_content[:10]]
                movie_scores = {mid: 100 for mid in movie_ids}  # All famous = high score
                
                print(f"   Got {len(movie_ids)} famous {content_type}s")
                return {'ids': movie_ids, 'scores': movie_scores}
            
            # Fallback: Get highest rated from cache
            imdb_cache = {}
            try:
                import json
                import os
                cache_path = os.path.join(os.path.dirname(__file__), '..', 'imdb_ratings_cache.json')
                if os.path.exists(cache_path):
                    with open(cache_path, 'r') as f:
                        imdb_cache = json.load(f)
            except:
                pass
            
            # Get content with ratings
            rated_content = []
            for item_title, rating_data in imdb_cache.items():
                if rating_data.get('rating', 0) >= 7.5:  # Only high-rated
                    try:
                        item = Model.objects(title=item_title).first()
                        if item and str(item.id) not in disliked_ids:
                            rated_content.append((item, rating_data['rating']))
                    except:
                        continue
            
            # Sort by rating
            rated_content.sort(key=lambda x: x[1], reverse=True)
            top_content = [item for item, rating in rated_content[:10]]
            
            movie_ids = [str(m.id) for m in top_content]
            movie_scores = {mid: int(rating * 10) for (m, rating), mid in zip(rated_content[:10], movie_ids)}
            
            print(f"   Got {len(movie_ids)} items")
            return {'ids': movie_ids, 'scores': movie_scores}
        except Exception as e:
            print(f"   Error getting top 10 {content_type}: {e}")
            return {'ids': [], 'scores': {}}
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 8: Top 20 Favorites
    # ═══════════════════════════════════════════════════════════════════════
    
    def _get_top_favorites(self, user_genres: List[str], disliked_ids: set, count: int = 20) -> Dict:
        """
        Top favorited MOVIES - Search ALL high-rated movies in database
        """
        try:
            # Get ALL high-rated movies (7.0+ rating) from database
            high_rated = list(Movie.objects(imdb_rating__gte=7.0).order_by('-imdb_rating'))
            
            print(f"   Searching {len(high_rated)} high-rated movies from database")
            
            # Filter dislikes
            content = [item for item in high_rated if str(item.id) not in disliked_ids]
            
            # Sort by user preferences using Smart AI
            sorted_content = self._sort_by_user_genres(content, user_genres, disliked_ids)
            
            content_ids = [str(c.id) for c in sorted_content[:count]]
            scores = {cid: 100 for cid in content_ids}
            
            print(f"   Selected {len(content_ids)} movies sorted by user taste")
            return {'ids': content_ids, 'scores': scores}
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return {'ids': [], 'scores': {}}
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 9-10: Newly Added Movies/Series
    # ═══════════════════════════════════════════════════════════════════════
    
    def _get_newly_added_movies(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get recently added movies - sorted by RELEASE YEAR (2023-2026)"""
        return self._get_newly_added('Movie', user_genres, disliked_ids)
    
    def _get_newly_added_series(self, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get recently added series - sorted by RELEASE YEAR (2023-2026)"""
        return self._get_newly_added('TV Show', user_genres, disliked_ids)
    
    def _get_newly_added(self, content_type: str, user_genres: List[str], disliked_ids: set) -> Dict:
        """Get ALL new content (2023-2026), sorted by user preferences"""
        try:
            Model = Movie if content_type == 'Movie' else TVShow
            
            # Get ALL content from 2023-2026
            new_content = list(Model.objects(release_year__gte=2023).order_by('-release_year', '-imdb_rating'))
            
            print(f"   Searching {len(new_content)} new {content_type}s (2023-2026) from database")
            
            # Filter dislikes
            new_content = [c for c in new_content if str(c.id) not in disliked_ids]
            
            # Sort by user preferences using Smart AI
            sorted_content = self._sort_by_user_genres(new_content, user_genres, disliked_ids)
            
            movie_ids = [str(m.id) for m in sorted_content[:self.SECTION_SIZE]]
            dates = {str(m.id): str(m.release_year) for m in sorted_content[:self.SECTION_SIZE]}
            
            print(f"   Selected {len(movie_ids)} {content_type}s sorted by user taste")
            return {'ids': movie_ids, 'dates': dates}
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return {'ids': [], 'dates': {}}
    
    # ═══════════════════════════════════════════════════════════════════════
    # HELPER: Sort by User Genres
    # ═══════════════════════════════════════════════════════════════════════
    
    def _sort_by_user_genres(self, content_list: list, user_genres: list, disliked_ids: set) -> list:
        """
        Sort content by user preferences with NETFLIX-STYLE WEIGHTED GENRE DISTRIBUTION
        
        🎯 NETFLIX APPROACH:
        - Primary genre (1st): 60-70% of recommendations (DOMINANT)
        - Secondary genre (2nd): 20-25% of recommendations (MODERATE)
        - Tertiary genre (3rd): 10-15% of recommendations (LIGHT)
        
        This gives users MOSTLY what they want (#1 genre) while adding variety (#2, #3)
        
        Strategy:
        - Genre 1: 800 pts (DOMINANT - ~60% weight)
        - Genre 2: 400 pts (MODERATE - ~30% weight)
        - Genre 3: 200 pts (LIGHT - ~15% weight)
        - Genre 4-5: 100 pts each (MINIMAL - ~8% each)
        - Primary match bonus: +300 pts (movie's 1st genre = user's genre)
        - Quality (IMDB): Max 30 pts
        - Popularity: Max 5 pts
        - Recency: Max 5 pts
        """
        import math
        content_list = [c for c in content_list if str(c.id) not in disliked_ids]

        imdb_cache = {}
        try:
            import json, os
            cache_path = os.path.join(os.path.dirname(__file__), "..", "imdb_ratings_cache.json")
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    imdb_cache = json.load(f)
        except Exception:
            pass

        user_genres_lower = [g.lower() for g in user_genres] if user_genres else []
        
        # ✅ BALANCED weights for better genre mix
        # Genre 1: 600 pts (~60% weight) - Primary but not overwhelming
        # Genre 2: 400 pts (~40% weight) - Secondary with strong presence
        # Genre 3: 200 pts (~20% weight) - Tertiary variety
        # Genre 4-5: 100 pts (~10% each) - Light variety
        #
        # OLD WEIGHTS [1200, 500, 200] were TOO EXTREME → 100% primary genre
        # NEW WEIGHTS [600, 400, 200] allow proper mixing → 60%/40% distribution
        weights = [600, 400, 200, 100, 100]

        def calculate_smart_score(content):
            genre_score = 0
            if user_genres_lower and hasattr(content, "listed_in") and content.listed_in:
                content_genres = [g.strip().lower() for g in content.listed_in.split(",") if g.strip()]
                
                # Weight genres by user priority (Netflix approach)
                for rank, user_genre in enumerate(user_genres_lower[:5]):
                    weight = weights[rank] if rank < len(weights) else 50
                    
                    for g_idx, content_genre in enumerate(content_genres):
                        is_match = (user_genre == content_genre or user_genre in content_genre or content_genre in user_genre)
                        if is_match:
                            genre_score += weight
                            
                            # Primary-to-Primary bonus: movie's FIRST genre matches user's genre
                            if g_idx == 0:
                                genre_score += 300
                            
                            break  # Only count once per user genre

            quality_score = 0
            title = getattr(content, "title", None)
            if title and title in imdb_cache:
                rating = imdb_cache[title].get("rating", 0)
                if rating > 0:
                    quality_score = min((rating - 5.0) * 6, 30)
            if quality_score == 0 and hasattr(content, "imdb_rating") and content.imdb_rating:
                try:
                    quality_score = min((float(content.imdb_rating) - 5.0) * 6, 30)
                except (ValueError, TypeError):
                    pass

            popularity_score = 0
            if title and title in imdb_cache:
                votes = imdb_cache[title].get("votes", 0)
                if votes > 0:
                    popularity_score = max(min(math.log10(votes) - 3, 5), 0)

            recency_score = 0
            year = getattr(content, "release_year", None)
            if year and year >= 2020:
                recency_score = min((year - 2019) * 0.8, 5)

            return genre_score + quality_score + popularity_score + recency_score

        return sorted(content_list, key=calculate_smart_score, reverse=True)
    
    def _sort_by_user_genres_with_trending(
        self, content_list: list, user_genres: list, disliked_ids: set, trending_scores: dict
    ) -> list:
        """
        Sort content by user preferences WITH TRENDING BOOST
        
        ✅ NEW: Adds trending score to the mix!
        
        Formula:
        - Genre Match: 600 pts (user's taste)
        - Trending Score: Up to 200 pts (global popularity)
        - Quality (IMDB): 30 pts
        - Popularity (votes): 5 pts
        - Recency: 5 pts
        
        Example: If "Joker" was watched by 100 users this week:
        - Trending = 100 watches × 10 pts = 1000 pts (capped at 200)
        - This boosts it significantly in rankings!
        """
        import math
        content_list = [c for c in content_list if str(c.id) not in disliked_ids]

        imdb_cache = {}
        try:
            import json, os
            cache_path = os.path.join(os.path.dirname(__file__), "..", "imdb_ratings_cache.json")
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    imdb_cache = json.load(f)
        except Exception:
            pass

        user_genres_lower = [g.lower() for g in user_genres] if user_genres else []
        weights = [600, 400, 200, 100, 100]

        def calculate_smart_score_with_trending(content):
            # Genre score (same as before)
            genre_score = 0
            if user_genres_lower and hasattr(content, "listed_in") and content.listed_in:
                content_genres = [g.strip().lower() for g in content.listed_in.split(",") if g.strip()]
                
                for rank, user_genre in enumerate(user_genres_lower[:5]):
                    weight = weights[rank] if rank < len(weights) else 50
                    
                    for g_idx, content_genre in enumerate(content_genres):
                        is_match = (user_genre == content_genre or user_genre in content_genre or content_genre in user_genre)
                        if is_match:
                            genre_score += weight
                            
                            if g_idx == 0:
                                genre_score += 300
                            
                            break

            # Quality score (same as before)
            quality_score = 0
            title = getattr(content, "title", None)
            if title and title in imdb_cache:
                rating = imdb_cache[title].get("rating", 0)
                if rating > 0:
                    quality_score = min((rating - 5.0) * 6, 30)
            if quality_score == 0 and hasattr(content, "imdb_rating") and content.imdb_rating:
                try:
                    quality_score = min((float(content.imdb_rating) - 5.0) * 6, 30)
                except (ValueError, TypeError):
                    pass

            # Popularity score (same as before)
            popularity_score = 0
            if title and title in imdb_cache:
                votes = imdb_cache[title].get("votes", 0)
                if votes > 0:
                    popularity_score = max(min(math.log10(votes) - 3, 5), 0)

            # Recency score (same as before)
            recency_score = 0
            year = getattr(content, "release_year", None)
            if year and year >= 2020:
                recency_score = min((year - 2019) * 0.8, 5)
            
            # ✅ NEW: Trending score!
            trending_score = 0
            movie_id = str(content.id)
            if movie_id in trending_scores:
                raw_trending = trending_scores[movie_id]
                # Cap at 200 pts so it doesn't overpower genre preferences
                trending_score = min(raw_trending / 5, 200)  # Divide by 5 to normalize

            return genre_score + quality_score + popularity_score + recency_score + trending_score

        return sorted(content_list, key=calculate_smart_score_with_trending, reverse=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SAVE TO MONGODB
    # ═══════════════════════════════════════════════════════════════════════
    
    def _create_sections(self, username: str, sections_data: Dict, user_genres: List[str]):
        """Create new personalized sections document"""
        sections = UserPersonalizedSections(
            username=username,
            
            # AI Recommendations
            ai_recommendations=sections_data['ai_recommendations']['ids'],
            ai_recommendations_metadata=sections_data['ai_recommendations']['metadata'],
            
            # Top Watched
            top_watched_movies=sections_data['top_watched_movies']['ids'],
            top_watched_movies_scores=sections_data['top_watched_movies']['scores'],
            top_watched_series=sections_data['top_watched_series']['ids'],
            top_watched_series_scores=sections_data['top_watched_series']['scores'],
            
            # Top Searched
            top_searched_movies=sections_data['top_searched_movies']['ids'],
            top_searched_movies_scores=sections_data['top_searched_movies']['scores'],
            top_searched_series=sections_data['top_searched_series']['ids'],
            top_searched_series_scores=sections_data['top_searched_series']['scores'],
            
            # Top 10
            top_10_movies=sections_data['top_10_movies']['ids'],
            top_10_movies_scores=sections_data['top_10_movies']['scores'],
            top_10_series=sections_data['top_10_series']['ids'],
            top_10_series_scores=sections_data['top_10_series']['scores'],
            
            # Top 20 Favorites
            top_20_favorites=sections_data['top_20_favorites']['ids'],
            top_20_favorites_scores=sections_data['top_20_favorites']['scores'],
            
            # Newly Added
            newly_added_movies=sections_data['newly_added_movies']['ids'],
            newly_added_movies_dates=sections_data['newly_added_movies']['dates'],
            newly_added_series=sections_data['newly_added_series']['ids'],
            newly_added_series_dates=sections_data['newly_added_series']['dates'],
            
            # Metadata
            user_preferred_genres=user_genres,
            last_updated=datetime.utcnow(),
            needs_update=False
        )
        sections.save()
    
    def _update_sections(self, existing: UserPersonalizedSections, sections_data: Dict, user_genres: List[str]):
        """Update existing sections document"""
        # AI Recommendations
        existing.ai_recommendations = sections_data['ai_recommendations']['ids']
        existing.ai_recommendations_metadata = sections_data['ai_recommendations']['metadata']
        
        # Top Watched
        existing.top_watched_movies = sections_data['top_watched_movies']['ids']
        existing.top_watched_movies_scores = sections_data['top_watched_movies']['scores']
        existing.top_watched_series = sections_data['top_watched_series']['ids']
        existing.top_watched_series_scores = sections_data['top_watched_series']['scores']
        
        # Top Searched
        existing.top_searched_movies = sections_data['top_searched_movies']['ids']
        existing.top_searched_movies_scores = sections_data['top_searched_movies']['scores']
        existing.top_searched_series = sections_data['top_searched_series']['ids']
        existing.top_searched_series_scores = sections_data['top_searched_series']['scores']
        
        # Top 10
        existing.top_10_movies = sections_data['top_10_movies']['ids']
        existing.top_10_movies_scores = sections_data['top_10_movies']['scores']
        existing.top_10_series = sections_data['top_10_series']['ids']
        existing.top_10_series_scores = sections_data['top_10_series']['scores']
        
        # Top 20 Favorites
        existing.top_20_favorites = sections_data['top_20_favorites']['ids']
        existing.top_20_favorites_scores = sections_data['top_20_favorites']['scores']
        
        # Newly Added
        existing.newly_added_movies = sections_data['newly_added_movies']['ids']
        existing.newly_added_movies_dates = sections_data['newly_added_movies']['dates']
        existing.newly_added_series = sections_data['newly_added_series']['ids']
        existing.newly_added_series_dates = sections_data['newly_added_series']['dates']
        
        # Metadata
        existing.user_preferred_genres = user_genres
        existing.last_updated = datetime.utcnow()
        existing.needs_update = False
        
        existing.save()
    
    def _sections_to_dict(self, sections: UserPersonalizedSections) -> Dict:
        """Convert sections document to dictionary"""
        return {
            'ai_recommendations': {
                'ids': sections.ai_recommendations,
                'metadata': sections.ai_recommendations_metadata
            },
            'top_watched_movies': {
                'ids': sections.top_watched_movies,
                'scores': sections.top_watched_movies_scores
            },
            'top_watched_series': {
                'ids': sections.top_watched_series,
                'scores': sections.top_watched_series_scores
            },
            'top_searched_movies': {
                'ids': sections.top_searched_movies,
                'scores': sections.top_searched_movies_scores
            },
            'top_searched_series': {
                'ids': sections.top_searched_series,
                'scores': sections.top_searched_series_scores
            },
            'top_10_movies': {
                'ids': sections.top_10_movies,
                'scores': sections.top_10_movies_scores
            },
            'top_10_series': {
                'ids': sections.top_10_series,
                'scores': sections.top_10_series_scores
            },
            'top_20_favorites': {
                'ids': sections.top_20_favorites,
                'scores': sections.top_20_favorites_scores
            },
            'newly_added_movies': {
                'ids': sections.newly_added_movies,
                'dates': sections.newly_added_movies_dates
            },
            'newly_added_series': {
                'ids': sections.newly_added_series,
                'dates': sections.newly_added_series_dates
            }
        }
    
    def _to_objectid(self, id_str: str):
        """Convert string ID to ObjectId"""
        from bson import ObjectId
        try:
            return ObjectId(id_str)
        except:
            return id_str

    def mark_sections_for_update(self, username: str, reason: str = 'manual'):
        """
        Mark user's personalized sections as needing update
        This will force regeneration next time sections are loaded
        
        Args:
            username: Username
            reason: Reason for update (e.g., 'favorites_changed', 'search_activity')
        """
        try:
            sections = UserPersonalizedSections.objects(username=username).first()
            if sections:
                sections.needs_update = True
                sections.update_reason = reason
                sections.save()
                print(f"✅ Marked sections for {username} as needing update (reason: {reason})")
            else:
                # If sections don't exist yet, they'll be created on next load
                print(f"ℹ️ No sections found for {username}, will create on next load")
        except Exception as e:
            print(f"❌ Error marking sections for update: {e}")
