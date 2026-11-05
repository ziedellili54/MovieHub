"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RECOMMENDATION FEEDBACK API - AI Self-Learning System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Track which recommendations users click for AI improvement
    Implements reinforcement learning through user feedback

ENDPOINTS:
    POST /api/analytics/recommendation-feedback/ - Track recommendation click
    GET /api/analytics/recommendation-stats/{username}/ - Get AI performance stats

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .analytics_models import RecommendationFeedback, UserPreferences
from datetime import datetime


class TrackRecommendationFeedbackView(APIView):
    """
    Track when user clicks a recommendation for AI learning
    
    POST /api/analytics/recommendation-feedback/
    
    Body:
    {
        "username": "john",
        "recommendation_batch_id": "rec_20260805_john_123456",
        "recommended_movie_id": "movie_id_123",
        "recommended_movie_title": "Inception",
        "recommendation_position": 15,  // Where in list (1-100)
        "similarity_score": 87.5,       // AI confidence
        "recommended_genres": ["Action", "Sci-Fi"],
        "user_favorite_genres_at_time": ["Action", "Thriller"],
        "total_recommendations_in_batch": 100,
        "recommended_at": "2026-08-05T10:00:00Z"
    }
    
    Response:
    {
        "success": true,
        "feedback_score": -5,  // Calculated score
        "feedback_category": "bad",
        "message": "Feedback recorded. AI will learn from this."
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            
            # Get required fields
            username = data.get('username')
            position = data.get('recommendation_position')
            
            if not username or not position:
                return Response({
                    'success': False,
                    'error': 'username and recommendation_position are required'
                }, status=400)
            
            # Calculate feedback score based on position
            feedback_score, feedback_category = self.calculate_feedback_score(position)
            
            # Calculate skipped count
            skipped_count = position - 1
            
            # Calculate time to click if timestamps provided
            time_to_click = None
            if data.get('recommended_at'):
                try:
                    recommended_at = datetime.fromisoformat(data.get('recommended_at').replace('Z', '+00:00'))
                    clicked_at = datetime.utcnow()
                    time_to_click = int((clicked_at - recommended_at).total_seconds())
                except:
                    pass
            
            # Get user's activity count for context
            from .analytics_models import UserActivity
            user_activity_count = UserActivity.objects(username=username).count()
            
            # Create feedback document
            feedback = RecommendationFeedback(
                username=username,
                recommendation_batch_id=data.get('recommendation_batch_id', f"rec_{datetime.utcnow().strftime('%Y%m%d')}_{username}"),
                recommended_movie_id=data.get('recommended_movie_id'),
                recommended_movie_title=data.get('recommended_movie_title'),
                recommendation_position=position,
                similarity_score=data.get('similarity_score'),
                recommended_genres=data.get('recommended_genres', []),
                feedback_score=feedback_score,
                feedback_category=feedback_category,
                user_favorite_genres_at_time=data.get('user_favorite_genres_at_time', []),
                user_activity_count=user_activity_count,
                total_recommendations_in_batch=data.get('total_recommendations_in_batch', 100),
                skipped_count=skipped_count,
                recommended_at=data.get('recommended_at') or datetime.utcnow(),
                clicked_at=datetime.utcnow(),
                time_to_click_seconds=time_to_click,
                timestamp=datetime.utcnow()
            )
            feedback.save()
            
            # ═════════════════════════════════════════════════════════════════
            # UPDATE USER PREFERENCES WITH AI LEARNING SCORES (PERMANENT STORAGE!)
            # ═════════════════════════════════════════════════════════════════
            try:
                # Get or create user preferences
                prefs, created = UserPreferences.objects.get_or_create(username=username)
                
                # Initialize recommendation_score if it doesn't exist
                if not prefs.recommendation_score:
                    prefs.recommendation_score = {}
                
                # Get genres from this feedback
                genres = data.get('recommended_genres', [])
                
                # Update genre scores based on feedback
                for i, genre in enumerate(genres[:3]):
                    if i == 0:
                        # Primary genre: full feedback impact (×3)
                        current_score = prefs.recommendation_score.get(genre, 0)
                        prefs.recommendation_score[genre] = current_score + (feedback_score * 3)
                    else:
                        # Secondary genres: half feedback impact (×1.5)
                        current_score = prefs.recommendation_score.get(genre, 0)
                        prefs.recommendation_score[genre] = current_score + (feedback_score * 1.5)
                
                # Update timestamp
                prefs.updated_at = datetime.utcnow()
                prefs.save()
                
                print(f"✅ Updated UserPreferences for {username}: {prefs.recommendation_score}")
                
            except Exception as e:
                print(f"⚠️ Could not update UserPreferences: {e}")
            
            # Return response with feedback details
            return Response({
                'success': True,
                'feedback_score': feedback_score,
                'feedback_category': feedback_category,
                'skipped_count': skipped_count,
                'message': self.get_feedback_message(feedback_category, position),
                'ai_will_learn': feedback_category in ['bad', 'very_bad']
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def calculate_feedback_score(self, position):
        """
        Calculate feedback score based on recommendation position
        
        SCORING SYSTEM:
        - Position 1-5:    +10 to +6 (EXCELLENT - AI nailed it)
        - Position 6-10:   +5 to +1 (GOOD - still top 10)
        - Position 11-20:  0 (NEUTRAL - acceptable)
        - Position 21-50:  -1 to -30 (BAD - skipped better options)
        - Position 51+:    -31 to -100 (VERY BAD - AI failed)
        
        Args:
            position (int): Where in recommendation list (1-100)
        
        Returns:
            tuple: (feedback_score, feedback_category)
        """
        if position <= 5:
            # Excellent: User clicked top 5
            feedback_score = 11 - position  # 10, 9, 8, 7, 6
            feedback_category = "excellent"
        elif position <= 10:
            # Good: User clicked top 10
            feedback_score = 11 - position  # 5, 4, 3, 2, 1
            feedback_category = "good"
        elif position <= 20:
            # Neutral: Acceptable range
            feedback_score = 0
            feedback_category = "neutral"
        elif position <= 50:
            # Bad: User skipped many better options
            feedback_score = 20 - position  # -1 to -30
            feedback_category = "bad"
        else:
            # Very Bad: AI really missed the mark
            feedback_score = 20 - (position * 2)  # -82 to -180
            feedback_category = "very_bad"
        
        return feedback_score, feedback_category
    
    def get_feedback_message(self, category, position):
        """Get human-readable feedback message"""
        messages = {
            "excellent": f"🎯 Perfect match! You clicked position {position}. AI is learning your preferences well.",
            "good": f"✅ Good recommendation! Position {position} is in top 10. AI is on track.",
            "neutral": f"👌 Decent match at position {position}. AI can improve.",
            "bad": f"⚠️ You skipped {position-1} better recommendations. AI will adjust.",
            "very_bad": f"❌ AI missed the mark. You skipped to position {position}. Learning from this mistake."
        }
        return messages.get(category, "Feedback recorded.")


class GetRecommendationStatsView(APIView):
    """
    Get AI performance statistics for a user
    
    GET /api/analytics/recommendation-stats/{username}/
    
    Response:
    {
        "success": true,
        "username": "john",
        "total_recommendations_clicked": 50,
        "average_position_clicked": 12.5,
        "average_feedback_score": 2.3,
        "feedback_distribution": {
            "excellent": 15,
            "good": 20,
            "neutral": 10,
            "bad": 4,
            "very_bad": 1
        },
        "ai_performance": "Good",  // Excellent, Good, Fair, Poor
        "improvement_over_time": "+15%",
        "recent_clicks": [...]
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            # Get all feedback for this user
            feedback_records = RecommendationFeedback.objects(username=username)
            
            if feedback_records.count() == 0:
                return Response({
                    'success': True,
                    'username': username,
                    'total_recommendations_clicked': 0,
                    'message': 'No recommendation feedback yet. Start clicking recommended movies!'
                })
            
            # Calculate statistics
            total_clicks = feedback_records.count()
            
            # Average position
            positions = [f.recommendation_position for f in feedback_records]
            avg_position = sum(positions) / len(positions) if positions else 0
            
            # Average feedback score
            scores = [f.feedback_score for f in feedback_records]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Feedback distribution
            distribution = {
                "excellent": 0,
                "good": 0,
                "neutral": 0,
                "bad": 0,
                "very_bad": 0
            }
            for f in feedback_records:
                if f.feedback_category in distribution:
                    distribution[f.feedback_category] += 1
            
            # Calculate AI performance rating
            if avg_score >= 5:
                performance = "Excellent"
            elif avg_score >= 2:
                performance = "Good"
            elif avg_score >= -2:
                performance = "Fair"
            else:
                performance = "Needs Improvement"
            
            # Recent clicks (last 10)
            recent_clicks = []
            for f in feedback_records.order_by('-clicked_at')[:10]:
                recent_clicks.append({
                    'movie_title': f.recommended_movie_title,
                    'position': f.recommendation_position,
                    'score': f.feedback_score,
                    'category': f.feedback_category,
                    'clicked_at': f.clicked_at.isoformat() if f.clicked_at else None
                })
            
            return Response({
                'success': True,
                'username': username,
                'total_recommendations_clicked': total_clicks,
                'average_position_clicked': round(avg_position, 1),
                'average_feedback_score': round(avg_score, 1),
                'feedback_distribution': distribution,
                'ai_performance': performance,
                'recent_clicks': recent_clicks
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 API ENDPOINTS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENDPOINT                                              METHOD  PURPOSE
────────────────────────────────────────────────────────────────────────────────
/api/analytics/recommendation-feedback/               POST    Track recommendation click
/api/analytics/recommendation-stats/{username}/       GET     Get AI performance stats

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
