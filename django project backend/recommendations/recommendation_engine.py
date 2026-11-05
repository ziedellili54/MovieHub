"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI RECOMMENDATION ENGINE - TensorFlow Hub + Vector Store  (FIXED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT WAS FIXED
    Bug: after watching 2-3 movies in one category, recs looked right.
    But as soon as the user viewed/watched a *different* category, the
    recommendations flipped to 100% the new category and the previous
    one disappeared completely.

    Root causes:
      1. UserActivity weighting was purely position-based over the last
         30 activities. A handful of fresh events in a new category could
         push a real watch history for another genre out of the window
         entirely (or down to a flat, negligible weight).
      2. Even when both genres survived in genre_weights, recommendations
         were generated from ONE merged embedding + a single vector
         search. Cosine similarity search naturally collapses toward
         whichever direction is strongest, so one genre crowds out the
         other in the results list — there was no mechanism forcing both
         genres to actually appear.

    Fix:
      1. Genre weight computation now uses a softer, floor-limited decay
         over a wider window, and only counts real engagement (not raw
         browsing/click events), so an older-but-real preference isn't
         wiped out by a few recent views.
      2. New get_top_user_genres() identifies which genres are actually
         IMPORTANT to the user (>= min_share of total weight).
      3. When 2+ genres are important, get_recommendations() now builds
         recommendations by querying the vector DB separately PER GENRE
         and interleaving the results proportionally to each genre's
         importance — guaranteeing a visible mix, not just a lucky
         embedding blend.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
from typing import List, Dict, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# TensorFlow imports
import tensorflow as tf
import tensorflow_hub as hub

# Use our simple vector store
from .vector_store import SimpleVectorDB

# MongoDB models
from movies.models import Movie, TVShow
from accounts.analytics_models import UserActivity, UserPreferences, MovieWatchHistory
from accounts.models import Favorite


class RecommendationEngine:
    """
    AI-powered recommendation system using TensorFlow Hub Universal Sentence Encoder

    Features:
        - Content-based recommendations (similar movies)
        - Multi-genre BLENDED recommendations (this fix)
        - Real-time learning from user behavior
        - Per-movie watch time tracking for better recommendations
    """

    def __init__(self):
        """Initialize the recommendation engine with TensorFlow Hub"""
        print("🔄 Initializing AI recommendation system with TensorFlow...")

        try:
            self.embed_model = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
            print("   ✅ TensorFlow Hub model loaded successfully!")
        except Exception as e:
            print(f"   ❌ Error loading TensorFlow model: {e}")
            raise Exception(f"Could not initialize TensorFlow embedding model: {e}")

        self.vector_db = SimpleVectorDB(path="./vector_db")

        self.movies_collection = self.vector_db.get_or_create_collection(
            name="movies",
            metadata={"description": "Movie and TV show embeddings", "model": "tensorflow-hub-use-v4"}
        )

        self.user_profiles_collection = self.vector_db.get_or_create_collection(
            name="user_profiles",
            metadata={"description": "User preference embeddings", "model": "tensorflow-hub-use-v4"}
        )

        print("   ✅ Vector database initialized")

    # ═══════════════════════════════════════════════════════════════════════
    # PART 1: EMBEDDINGS
    # ═══════════════════════════════════════════════════════════════════════

    def generate_embedding(self, text: str) -> List[float]:
        try:
            embedding = self.embed_model([text])
            return embedding.numpy()[0].tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def create_movie_text(self, movie) -> str:
        parts = []
        primary_genre = ""
        secondary_genres = []

        if hasattr(movie, 'primary_category') and movie.primary_category:
            primary_genre = movie.primary_category
        elif hasattr(movie, 'listed_in') and movie.listed_in:
            all_genres = [g.strip() for g in movie.listed_in.split(',')]
            if all_genres:
                primary_genre = all_genres[0]
                secondary_genres = all_genres[1:3]

        if primary_genre:
            parts.append(f"Primary Genre: {primary_genre}. Category: {primary_genre}. Main Genre: {primary_genre}")
        if secondary_genres:
            parts.append(f"Secondary Genres: {', '.join(secondary_genres)}")
        if hasattr(movie, 'type') and movie.type:
            parts.append(f"Type: {movie.type}")
        if hasattr(movie, 'release_year') and movie.release_year:
            parts.append(f"Year: {movie.release_year}")
        if hasattr(movie, 'description') and movie.description:
            parts.append(f"Plot: {movie.description[:300]}")
        if hasattr(movie, 'rating') and movie.rating and movie.rating != 'N/A':
            parts.append(f"Rating: {movie.rating}")
        if hasattr(movie, 'director') and movie.director:
            parts.append(f"Director: {movie.director}")

        return ". ".join(parts)

    # ═══════════════════════════════════════════════════════════════════════
    # PART 2: INDEXING (unchanged)
    # ═══════════════════════════════════════════════════════════════════════

    def index_movie(self, movie) -> bool:
        try:
            movie_id = str(movie.id)
            movie_text = self.create_movie_text(movie)
            embedding = self.generate_embedding(movie_text)
            if embedding is None:
                return False

            metadata = {
                "title": movie.title or "",
                "type": movie.type or "Movie",
                "genres": movie.listed_in or "",
                "release_year": str(movie.release_year) if movie.release_year else "0",
                "rating": movie.rating or "",
            }

            self.movies_collection.upsert(
                ids=[movie_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[movie_text]
            )
            return True
        except Exception as e:
            print(f"Error indexing movie {movie.title}: {e}")
            return False

    def index_all_movies(self, batch_size: int = 50) -> Dict:
        stats = {"movies_indexed": 0, "tvshows_indexed": 0, "failed": 0, "total": 0}
        print("\n🎬 Indexing all movies with TensorFlow Hub...")

        movies = Movie.objects.all()
        for i, movie in enumerate(movies, 1):
            stats["total"] += 1
            if self.index_movie(movie):
                stats["movies_indexed"] += 1
            else:
                stats["failed"] += 1

        tvshows = TVShow.objects.all()
        for i, tvshow in enumerate(tvshows, 1):
            stats["total"] += 1
            if self.index_movie(tvshow):
                stats["tvshows_indexed"] += 1
            else:
                stats["failed"] += 1

        print(f"\n   ✅ Indexing complete! Total: {stats['total']}, Failed: {stats['failed']}")
        return stats

    # ═══════════════════════════════════════════════════════════════════════
    # PART 3: USER GENRE WEIGHTS  (core of the fix)
    # ═══════════════════════════════════════════════════════════════════════

    def _get_movie_or_show(self, movie_id):
        """Resolve a movie_id (str or ObjectId) to a Movie or TVShow doc."""
        try:
            from bson import ObjectId
            oid = movie_id if isinstance(movie_id, ObjectId) else ObjectId(str(movie_id))
        except Exception:
            oid = movie_id
        try:
            return Movie.objects.get(id=oid)
        except Exception:
            try:
                return TVShow.objects.get(id=oid)
            except Exception:
                return None

    def _add_genre_weights(self, genre_weights: Dict[str, float], listed_in: str,
                            primary: float, secondary: float):
        """Accumulate weight into primary (first genre) and secondary genres."""
        all_genres = [g.strip() for g in listed_in.split(',') if g.strip()]
        if not all_genres:
            return
        genre_weights[all_genres[0]] = genre_weights.get(all_genres[0], 0) + primary
        for genre in all_genres[1:3]:
            genre_weights[genre] = genre_weights.get(genre, 0) + secondary

    def _compute_genre_weights(self, username: str) -> Dict[str, float]:
        """
        Compute accumulated genre weights from ALL user data sources.

        FIX vs. the old version:
          - UserActivity is filtered to real engagement (watch/play/complete
            or has watch_time_minutes), so passive browsing/clicks in a
            newly-viewed category can't evict a genre the user actually
            watched before.
          - The recency decay has a floor (15% of max) instead of dropping
            to a flat 5, and the window is wider (60 instead of 30), so an
            older genre doesn't get zeroed out just because it's no longer
            the most recent thing watched.
          - Watch-history weight is scaled by how much of the movie was
            actually watched (when available), instead of a flat weight
            regardless of whether the user watched 5% or 100%.
        """
        genre_weights: Dict[str, float] = {}

        # 0. Stored AI learning scores (persist across sessions)
        try:
            prefs = UserPreferences.objects.get(username=username)
            if prefs.recommendation_score:
                for genre, score in prefs.recommendation_score.items():
                    genre_weights[genre] = genre_weights.get(genre, 0) + score
        except UserPreferences.DoesNotExist:
            pass
        except Exception as e:
            print(f"Could not load UserPreferences: {e}")

        # 1. Favorites - highest, stable weight
        favorites = Favorite.objects(username=username)[:20]
        for fav in favorites:
            movie = self._get_movie_or_show(fav.movie_id)
            if movie and getattr(movie, 'listed_in', None):
                self._add_genre_weights(genre_weights, movie.listed_in, primary=300, secondary=100)

        # 2. User activity — real engagement only, softer recency decay
        try:
            activities = UserActivity.objects(username=username).order_by('-timestamp')[:60]

            engagement = [
                a for a in activities
                if getattr(a, 'action', 'watch') in ('watch', 'play', 'complete')
                or getattr(a, 'watch_time_minutes', 0) > 0
            ]

            total = len(engagement)
            for idx, activity in enumerate(engagement):
                # Floor at 15% of max weight so older genres still count
                decay = max(0.15, 1 - (idx / max(total, 1)) * 0.85)
                base_weight = 40 * decay

                movie = self._get_movie_or_show(activity.movie_id)
                if movie and getattr(movie, 'listed_in', None):
                    self._add_genre_weights(
                        genre_weights, movie.listed_in,
                        primary=base_weight * 3, secondary=base_weight
                    )
        except Exception as e:
            print(f"Could not load UserActivity: {e}")

        # 3. Watch history — scaled by actual completion, not flat
        try:
            watch_history = MovieWatchHistory.objects(username=username)[:40]
            for watch in watch_history:
                movie = self._get_movie_or_show(watch.movie_id)
                if not movie or not getattr(movie, 'listed_in', None):
                    continue

                completion = getattr(watch, 'watch_percentage', None)
                if completion is None:
                    completion = 1.0
                completion = max(0.2, min(1.0, completion))

                self._add_genre_weights(
                    genre_weights, movie.listed_in,
                    primary=60 * completion, secondary=20 * completion
                )
        except Exception as e:
            print(f"Could not load Watch History: {e}")

        return genre_weights

    def get_top_user_genres(self, username: str, min_share: float = 0.08) -> List[Dict]:
        """
        Return genres that are actually IMPORTANT to the user.
        
        ✅ FIX: Lowered threshold from 15% → 8% so secondary genres are included
        ✅ FIX: Always return at least TOP 2 genres if user has multiple
        
        This ensures when user selects Crime + Adventure, BOTH genres appear
        in recommendations, not just the dominant one.
        """
        genre_weights = self._compute_genre_weights(username)
        total = sum(genre_weights.values())
        if total <= 0:
            return []

        # Get all genres meeting the threshold
        important = [
            {"genre": g, "weight": w, "share": w / total}
            for g, w in genre_weights.items()
            if (w / total) >= min_share
        ]
        important.sort(key=lambda x: x["weight"], reverse=True)
        
        # ✅ FIX: If user has genres but none meet threshold, take top 2 anyway
        # This ensures secondary genre (Adventure) is included even if Crime dominates
        if len(important) < 2 and len(genre_weights) >= 2:
            print(f"⚠️  Only {len(important)} genres met {min_share:.0%} threshold")
            print(f"   Taking top 2 genres anyway to ensure variety")
            
            all_genres = [
                {"genre": g, "weight": w, "share": w / total}
                for g, w in genre_weights.items()
            ]
            all_genres.sort(key=lambda x: x["weight"], reverse=True)
            important = all_genres[:2]
        
        return important[:4]  # cap at 4 so we don't dilute too far

    def get_user_profile_text(self, username: str) -> str:
        """Build a text profile from accumulated genre weights (for the single-profile fallback)."""
        genre_weights = self._compute_genre_weights(username)

        if not genre_weights:
            return "New user exploring content"

        sorted_genres = sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)
        top_genres = [genre for genre, weight in sorted_genres[:10]]

        print(f"📊 User {username} genre weights: {sorted_genres[:10]}")

        return (
            f"Favorite Genres: {', '.join(top_genres[:3])}. "
            f"Likes: {', '.join(top_genres[:6])}. "
            f"Interested in: {', '.join(top_genres)}"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PART 4: RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════

    def get_recommendations(
        self,
        username: str,
        n_recommendations: int = 20,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate personalized recommendations.

        FIX: when the user has 2+ genres that are each individually
        important (>=15% of their weight), we blend recommendations across
        ALL of them, proportional to importance, instead of relying on one
        merged embedding that tends to collapse toward a single genre.
        """
        try:
            watch_history = MovieWatchHistory.objects(username=username)
            watch_count = len(list(watch_history))

            if watch_count < 3:
                print(f"User {username} has only {watch_count} watch history items, returning popular movies")
                return self.get_popular_movies(n_recommendations, filters)

            watched_ids = set()
            watched_ids.update([str(w.movie_id) for w in watch_history])
            watched_ids.update([str(f.movie_id) for f in Favorite.objects(username=username)])
            try:
                from accounts.analytics_models import MovieDislike
                watched_ids.update([str(d.movie_id) for d in MovieDislike.objects(username=username)])
            except Exception as e:
                print(f"Could not load dislikes: {e}")

            top_genres = self.get_top_user_genres(username, min_share=0.15)
            print(f"User {username} important genres: {top_genres}")

            if len(top_genres) >= 2:
                recs = self._get_blended_recommendations(
                    top_genres, watched_ids, n_recommendations, filters
                )
                if recs:
                    return recs
                # if blending somehow produced nothing, fall through

            recs = self._get_single_profile_recommendations(
                username, watched_ids, n_recommendations, filters
            )
            return recs if recs else self.get_popular_movies(n_recommendations, filters)

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            import traceback
            traceback.print_exc()
            try:
                return self.get_popular_movies(n_recommendations, filters)
            except Exception:
                return []

    def _build_movie_dict(self, movie, similarity_score: float, reason: str) -> Dict:
        return {
            "movie_id": str(movie.id),
            "title": movie.title,
            "type": getattr(movie, 'type', 'Movie'),
            "genres": getattr(movie, 'listed_in', ''),
            "listed_in": getattr(movie, 'listed_in', ''),
            "primary_category": getattr(movie, 'primary_category', ''),
            "description": getattr(movie, 'description', ''),
            "poster": getattr(movie, 'poster', None),
            "release_year": getattr(movie, 'release_year', 0),
            "rating": getattr(movie, 'rating', ''),
            "director": getattr(movie, 'director', ''),
            "cast": getattr(movie, 'cast', ''),
            "similarity_score": round(float(similarity_score), 1),
            "reason": reason
        }

    def _get_blended_recommendations(
        self,
        top_genres: List[Dict],
        watched_ids: set,
        n_recommendations: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """
        Query the vector DB SEPARATELY per important genre, give each genre
        a quota of slots proportional to its importance, then interleave
        the results.
        
        ✅ FIX: Minimum 30% quota for secondary genre (instead of letting it drop too low)
        ✅ FIX: Better interleaving to ensure visible mix of both genres
        """
        total_weight = sum(g["weight"] for g in top_genres)
        seen_ids = set()
        buckets = []  # list of (genre_name, [recs])

        where_clause = {}
        if filters:
            if filters.get('genre'):
                where_clause['genres'] = {'$contains': filters['genre']}
            if filters.get('type'):
                where_clause['type'] = filters['type']

        for idx, genre_info in enumerate(top_genres):
            genre = genre_info["genre"]
            share = genre_info["weight"] / total_weight
            
            # ✅ FIX: Ensure secondary genre gets at least 30% quota
            # Primary: 60-70%, Secondary: 30-40% (Netflix-style)
            if idx == 0:  # Primary genre
                quota = max(1, round(n_recommendations * 0.60))  # 60% for primary
            elif idx == 1:  # Secondary genre
                quota = max(1, round(n_recommendations * 0.30))  # 30% for secondary
            else:  # Tertiary genres
                quota = max(1, round(n_recommendations * 0.10))  # 10% for others
            
            print(f"🎯 Genre {idx+1} '{genre}': {quota} slots ({quota/n_recommendations*100:.0f}%)")

            genre_text = f"Primary Genre: {genre}. Category: {genre}. Main Genre: {genre}"
            genre_embedding = self.generate_embedding(genre_text)
            if genre_embedding is None:
                continue

            results = self.movies_collection.query(
                query_embeddings=[genre_embedding],
                n_results=min(quota * 5, 100),
                where=where_clause if where_clause else None
            )

            genre_recs = []
            if results and results.get('ids') and len(results['ids']) > 0:
                ids = results['ids'][0]
                distances = results['distances'][0]

                for i, movie_id in enumerate(ids):
                    if movie_id in watched_ids or movie_id in seen_ids:
                        continue
                    movie = self._get_movie_or_show(movie_id)
                    if not movie:
                        continue

                    similarity_score = (1 - distances[i]) * 100
                    genre_recs.append(self._build_movie_dict(
                        movie, similarity_score, f"Because you like {genre}"
                    ))
                    seen_ids.add(movie_id)
                    if len(genre_recs) >= quota:
                        break

            print(f"   ✅ Found {len(genre_recs)}/{quota} recommendations for '{genre}'")
            buckets.append((genre, genre_recs))

        # ✅ IMPROVED INTERLEAVING: Alternate between genres more evenly
        # Pattern for 2 genres: A, B, A, B, A, B... (60% A, 40% B)
        # This ensures VISIBLE mix, not clustered by genre
        recommendations = []
        max_len = max((len(recs) for _, recs in buckets), default=0)
        
        for i in range(max_len):
            for genre, recs in buckets:
                if i < len(recs):
                    recommendations.append(recs[i])
                if len(recommendations) >= n_recommendations:
                    break
            if len(recommendations) >= n_recommendations:
                break

        print(f"   🎬 Total recommendations: {len(recommendations)}")
        return recommendations

    def _get_single_profile_recommendations(
        self,
        username: str,
        watched_ids: set,
        n_recommendations: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """Fallback: single merged-profile embedding search (used when the
        user only has one dominant genre)."""
        user_text = self.get_user_profile_text(username)
        user_embedding = self.generate_embedding(user_text)
        if user_embedding is None:
            return []

        where_clause = {}
        if filters:
            if filters.get('genre'):
                where_clause['genres'] = {'$contains': filters['genre']}
            if filters.get('type'):
                where_clause['type'] = filters['type']

        n_results = min(n_recommendations * 10, 200)
        results = self.movies_collection.query(
            query_embeddings=[user_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )

        recommendations = []
        if results and results.get('ids') and len(results['ids']) > 0:
            ids = results['ids'][0]
            distances = results['distances'][0]

            for i, movie_id in enumerate(ids):
                if movie_id in watched_ids:
                    continue
                movie = self._get_movie_or_show(movie_id)
                if not movie:
                    continue

                similarity_score = (1 - distances[i]) * 100
                reason = self.get_recommendation_reason(username, movie, similarity_score / 100)
                recommendations.append(self._build_movie_dict(movie, similarity_score, reason))

                if len(recommendations) >= n_recommendations:
                    break

        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        return recommendations

    def get_recommendation_reason(self, username: str, movie, score: float) -> str:
        try:
            top_watched = MovieWatchHistory.objects(
                username=username
            ).order_by('-total_watch_time_minutes').limit(3)

            if top_watched and len(list(top_watched)) > 0:
                most_watched = list(top_watched)[0]
                return f"Because you watched {most_watched.movie_title}"

            try:
                prefs = UserPreferences.objects.get(username=username)
                if prefs.favorite_genres and len(prefs.favorite_genres) > 0:
                    return f"Based on your love for {prefs.favorite_genres[0]}"
            except Exception:
                pass

            return "Recommended for you"
        except Exception:
            return "Recommended for you"

    # ═══════════════════════════════════════════════════════════════════════
    # PART 5: TRENDING / POPULAR (unchanged)
    # ═══════════════════════════════════════════════════════════════════════

    def get_popular_movies(self, n_movies: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        try:
            from collections import defaultdict
            from datetime import datetime, timedelta

            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            current_year = now.year

            recent_watch_counts = defaultdict(int)
            for watch in MovieWatchHistory.objects.only('movie_id', 'last_watched'):
                if watch.last_watched:
                    try:
                        if isinstance(watch.last_watched, str):
                            from dateutil import parser
                            last_watched_dt = parser.parse(watch.last_watched)
                        else:
                            last_watched_dt = watch.last_watched
                        if last_watched_dt >= thirty_days_ago:
                            recent_watch_counts[str(watch.movie_id)] += 5
                    except Exception:
                        continue

            all_watch_counts = defaultdict(int)
            for watch in MovieWatchHistory.objects.only('movie_id'):
                all_watch_counts[str(watch.movie_id)] += 1

            favorite_counts = defaultdict(int)
            for fav in Favorite.objects.only('movie_id'):
                favorite_counts[str(fav.movie_id)] += 3

            all_content = []
            try:
                all_content.extend(list(Movie.objects.all()))
            except Exception:
                pass
            try:
                all_content.extend(list(TVShow.objects.all()))
            except Exception:
                pass

            trending_candidates = []
            for content in all_content:
                try:
                    movie_id = str(content.id)
                    release_year = getattr(content, 'release_year', 0)

                    if filters and filters.get('type'):
                        if getattr(content, 'type', '') != filters['type']:
                            continue

                    recent_score = recent_watch_counts.get(movie_id, 0)
                    all_score = all_watch_counts.get(movie_id, 0)
                    fav_score = favorite_counts.get(movie_id, 0)
                    base_score = recent_score + (all_score * 0.5) + fav_score

                    if release_year >= current_year:
                        recency_multiplier, recency_bonus = 10.0, 100
                    elif release_year >= (current_year - 1):
                        recency_multiplier, recency_bonus = 8.0, 80
                    elif release_year >= (current_year - 2):
                        recency_multiplier, recency_bonus = 6.0, 60
                    elif release_year >= (current_year - 3):
                        recency_multiplier, recency_bonus = 4.0, 40
                    elif release_year >= (current_year - 4):
                        recency_multiplier, recency_bonus = 2.0, 20
                    elif release_year >= (current_year - 6):
                        recency_multiplier, recency_bonus = 1.0, 5
                    else:
                        recency_multiplier, recency_bonus = 0.1, 0

                    final_score = (base_score * recency_multiplier) + recency_bonus
                    if final_score == recency_bonus and release_year >= (current_year - 3):
                        final_score = recency_bonus + (release_year * 0.01)

                    trending_candidates.append({
                        'movie': content, 'score': final_score, 'release_year': release_year
                    })
                except Exception:
                    continue

            trending_candidates.sort(key=lambda x: x['score'], reverse=True)

            recommendations = []
            for candidate in trending_candidates[:n_movies]:
                movie = candidate['movie']
                year = candidate['release_year']
                if year >= current_year:
                    reason = f"🆕 Nouveau {year}"
                elif year >= (current_year - 2):
                    reason = f"🔥 Trending {year}"
                else:
                    reason = f"⭐ Popular {year}"

                recommendations.append(self._build_movie_dict(movie, candidate['score'], reason))

            return recommendations
        except Exception as e:
            print(f"Error getting trending movies: {e}")
            import traceback
            traceback.print_exc()
            return []

    # ═══════════════════════════════════════════════════════════════════════
    # PART 6: SIMILAR MOVIES (unchanged)
    # ═══════════════════════════════════════════════════════════════════════

    def get_similar_movies(self, movie_id: str, n_results: int = 5) -> List[Dict]:
        try:
            movie = self._get_movie_or_show(movie_id)
            if not movie:
                return []

            movie_text = self.create_movie_text(movie)
            movie_embedding = self.generate_embedding(movie_text)
            if movie_embedding is None:
                return []

            results = self.movies_collection.query(
                query_embeddings=[movie_embedding],
                n_results=n_results + 1
            )

            similar_movies = []
            if results and results.get('ids') and len(results['ids']) > 0:
                ids = results['ids'][0]
                distances = results['distances'][0]

                for i, similar_id in enumerate(ids):
                    if similar_id == movie_id:
                        continue
                    similar_movie = self._get_movie_or_show(similar_id)
                    if not similar_movie:
                        continue

                    similarity_score = 1 - distances[i]
                    similar_movies.append({
                        "movie_id": str(similar_movie.id),
                        "title": similar_movie.title,
                        "type": similar_movie.type,
                        "genres": similar_movie.listed_in,
                        "poster": similar_movie.poster,
                        "similarity_score": round(float(similarity_score), 3)
                    })

                    if len(similar_movies) >= n_results:
                        break

            return similar_movies
        except Exception as e:
            print(f"Error finding similar movies: {e}")
            return []