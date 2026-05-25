"""
Advanced Adaptive Learning System for Bank LLM - Database-Backed Version
Using PostgreSQL/SQLite via SQLAlchemy ORM

Components:
- Query rewriting based on poor performance
- User profile learning and personalization
- Semantic query clustering for pattern recognition
- Adaptive retrieval parameters per user/domain
- Answer quality prediction and ranking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import uuid
from difflib import SequenceMatcher

from database import (
    SessionLocal, UserProfile, QueryCache, PerformanceMetric,
    QueryRewrite, Feedback, OptimizationInsight
)

logger = logging.getLogger(__name__)


# ─── Query Rewriting ──────────────────────────────────────────────────────────

class QueryRewriter:
    """Learn from poor-performing queries and suggest improvements."""
    
    def record_rewrite(self, original: str, rewritten: str, original_rating: int, 
                      rewritten_rating: int, strategy: str = "default") -> Dict:
        """Record a successful or failed query rewrite."""
        db = SessionLocal()
        try:
            rewrite_id = hashlib.md5(
                f"{original}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            
            rewrite = QueryRewrite(
                id=rewrite_id,
                original_query=original,
                rewritten_query=rewritten,
                original_rating=original_rating,
                rewritten_rating=rewritten_rating,
                improvement=rewritten_rating - original_rating,
                successful=rewritten_rating > original_rating,
                rewrite_strategy=strategy,
            )
            db.add(rewrite)
            db.commit()
            
            logger.info(f"Recorded query rewrite: {strategy} | Improvement: {rewrite.improvement}")
            return rewrite.to_dict()
        except Exception as e:
            logger.error(f"Error recording rewrite: {e}")
            db.rollback()
            return {}
        finally:
            db.close()
    
    def suggest_rewrite(self, query: str) -> Optional[str]:
        """
        Suggest improved version of a query based on learned patterns.
        
        Strategies:
        1. Add banking-specific terminology
        2. Simplify complex queries
        3. Add context from similar high-rated queries
        4. Break down compound questions
        """
        query_lower = query.lower()
        
        # Strategy 1: Add banking terminology if absent
        banking_terms = {
            "loan": ["credit facility", "advance", "borrowing"],
            "deposit": ["savings", "term deposit", "fixed deposit"],
            "rate": ["interest rate", "repo rate", "policy rate"],
            "compliance": ["regulatory requirement", "RBI guideline"],
            "kyc": ["know your customer", "customer identification"],
            "aml": ["anti-money laundering", "money laundering prevention"],
        }
        
        for term, alternatives in banking_terms.items():
            if term in query_lower:
                return f"{query} (regulatory reference)"
        
        # Strategy 2: If query is very long, break it down
        if len(query) > 150:
            words = query.split()
            if len(words) > 20:
                core_query = " ".join(words[:15])
                return f"{core_query}?"
        
        return None


# ─── User Profile Management ──────────────────────────────────────────────────

class UserProfileManager:
    """Track user preferences and personalize RAG parameters."""
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one."""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter_by(id=user_id).first()
            if not profile:
                profile = UserProfile(id=user_id)
                db.add(profile)
                db.commit()
                logger.info(f"Created new user profile: {user_id}")
            return profile
        finally:
            db.close()
    
    def update_user_profile(self, user_id: str, topic: str, rating: int, 
                           response_time_ms: int = 0, sources: List = None) -> Dict:
        """Update user profile with interaction data."""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter_by(id=user_id).first()
            if not profile:
                profile = UserProfile(
                    id=user_id,
                    common_topics={},
                    total_interactions=0,
                    avg_rating=0.0,
                    top_k=5,
                    similarity_threshold=0.7,
                    use_cache=True,
                )
                db.add(profile)
            
            # Update topics
            if isinstance(profile.common_topics, dict):
                profile.common_topics[topic] = profile.common_topics.get(topic, 0) + 1
            else:
                profile.common_topics = {topic: 1}
            
            # Update interaction count and average rating
            profile.total_interactions += 1
            if profile.avg_rating == 0:
                profile.avg_rating = float(rating)
            else:
                profile.avg_rating = (
                    (profile.avg_rating * (profile.total_interactions - 1) + rating) 
                    / profile.total_interactions
                )
            
            # Adaptive parameters: increase top_k if user prefers diverse results
            if sources and len(sources) > profile.top_k:
                profile.top_k = min(profile.top_k + 1, 20)
            
            # Adjust similarity threshold based on rating pattern
            if rating >= 4:
                profile.similarity_threshold = max(0.5, profile.similarity_threshold - 0.05)
            elif rating <= 2:
                profile.similarity_threshold = min(0.9, profile.similarity_threshold + 0.05)
            
            profile.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Updated profile {user_id}: avg_rating={profile.avg_rating:.2f}, top_k={profile.top_k}")
            return profile.to_dict()
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            db.rollback()
            return {}
        finally:
            db.close()
    
    def get_personalized_params(self, user_id: str) -> Dict:
        """Get RAG parameters personalized for user."""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter_by(id=user_id).first()
            if not profile:
                # Return defaults
                return {
                    "top_k": 5,
                    "similarity_threshold": 0.7,
                    "use_cache": True,
                }
            
            return {
                "top_k": profile.top_k,
                "similarity_threshold": profile.similarity_threshold,
                "use_cache": profile.use_cache,
            }
        finally:
            db.close()
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile data."""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter_by(id=user_id).first()
            if not profile:
                return {}
            return profile.to_dict()
        finally:
            db.close()
    
    def get_all_user_stats(self) -> Dict:
        """Get statistics across all users."""
        db = SessionLocal()
        try:
            total_users = db.query(UserProfile).count()
            total_interactions = db.query(UserProfile).with_entities(
                UserProfile.total_interactions
            ).all()
            total_inter_sum = sum([t[0] for t in total_interactions])
            
            # Get average rating across all users
            avg_ratings = db.query(UserProfile).with_entities(
                UserProfile.avg_rating
            ).all()
            users_with_data = [r[0] for r in avg_ratings if r[0] > 0]
            avg_rating_all = sum(users_with_data) / len(users_with_data) if users_with_data else 0
            
            # Count active users in last 24h
            cutoff_date = datetime.utcnow() - timedelta(hours=24)
            active_24h = db.query(UserProfile).filter(
                UserProfile.updated_at >= cutoff_date
            ).count()
            
            return {
                "total_users": total_users,
                "total_interactions": total_inter_sum,
                "avg_rating_all_users": round(avg_rating_all, 2),
                "active_users_24h": active_24h,
            }
        finally:
            db.close()


# ─── Query Caching & Clustering ───────────────────────────────────────────────

class QueryClusteringEngine:
    """Cache high-quality answers and find similar cached queries."""
    
    SIMILARITY_THRESHOLD = 0.85  # 85% match for considering as "similar"
    
    def find_similar_cached(self, query: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """Find similar query in cache."""
        db = SessionLocal()
        try:
            # Get recent cached queries (within last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            cached_queries = db.query(QueryCache).filter(
                QueryCache.created_at >= cutoff_date,
                QueryCache.rating >= 4
            ).all()
            
            for cached in cached_queries:
                similarity = self._calculate_similarity(query, cached.query)
                if similarity >= self.SIMILARITY_THRESHOLD:
                    # Update hit count
                    cached.hit_count += 1
                    cached.last_accessed = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Cache hit: {similarity:.2%} similarity | Topic: {cached.topic}")
                    return {
                        "cached": True,
                        "answer": cached.answer,
                        "sources": cached.sources,
                        "topic": cached.topic,
                        "generation_time_ms": 5,  # Nearly instant
                        "similarity_score": similarity,
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error finding cached query: {e}")
            return None
        finally:
            db.close()
    
    def cache_query(self, query: str, answer: str, rating: int, sources: List,
                   topic: str = "general", user_id: Optional[str] = None,
                   generation_time_ms: int = 0) -> bool:
        """Cache high-quality answers (rating >= 4)."""
        if rating < 4:
            return False
        
        db = SessionLocal()
        try:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            existing = db.query(QueryCache).filter_by(id=query_hash).first()
            if existing:
                # Update existing cache entry
                existing.hit_count = 0
                existing.avg_rating = rating
                existing.updated_at = datetime.utcnow()
            else:
                # Create new cache entry
                cache = QueryCache(
                    id=query_hash,
                    query=query,
                    answer=answer,
                    sources=sources,
                    rating=rating,
                    topic=topic,
                    user_id=user_id,
                    generation_time_ms=generation_time_ms,
                )
                db.add(cache)
            
            db.commit()
            logger.info(f"Cached query: {topic} | Rating: {rating}⭐")
            return True
        except Exception as e:
            logger.error(f"Error caching query: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    @staticmethod
    def _calculate_similarity(query1: str, query2: str) -> float:
        """Calculate semantic similarity between two queries."""
        matcher = SequenceMatcher(None, query1.lower(), query2.lower())
        return matcher.ratio()
    
    def get_cache_stats(self) -> Dict:
        """Get caching statistics."""
        db = SessionLocal()
        try:
            total_cached = db.query(QueryCache).count()
            total_accesses = sum([c.hit_count for c in db.query(QueryCache).all()])
            avg_rating = 0.0
            
            if total_cached > 0:
                ratings = db.query(QueryCache).with_entities(QueryCache.avg_rating).all()
                avg_rating = sum([r[0] for r in ratings]) / len(ratings) if ratings else 0
            
            cache_hits = db.query(PerformanceMetric).with_entities(
                PerformanceMetric.cache_hits
            ).all()
            cache_misses = db.query(PerformanceMetric).with_entities(
                PerformanceMetric.cache_misses
            ).all()
            
            total_hits = sum([h[0] for h in cache_hits]) if cache_hits else 0
            total_misses = sum([m[0] for m in cache_misses]) if cache_misses else 0
            hit_rate = (total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0
            
            return {
                "total_cached_queries": total_cached,
                "total_cache_hits": total_hits,
                "hit_rate": round(hit_rate, 2),
                "avg_rating_cached": round(avg_rating, 2),
            }
        finally:
            db.close()


# ─── Performance Metrics ──────────────────────────────────────────────────────

class PerformanceMetrics:
    """Track system performance by topic."""
    
    def record_interaction(self, topic: str, rating: int, response_time_ms: int,
                          cache_hit: bool = False) -> Dict:
        """Record an interaction for metrics."""
        db = SessionLocal()
        try:
            date_str = datetime.utcnow().date().isoformat()
            metric_id = f"{topic}_{date_str}"
            
            metric = db.query(PerformanceMetric).filter_by(id=metric_id).first()
            if not metric:
                metric = PerformanceMetric(
                    id=metric_id,
                    topic=topic,
                    date=date_str,
                    total_queries=0,
                    avg_response_time=0.0,
                    avg_rating=0.0,
                    cache_hits=0,
                    cache_misses=0,
                    ratings_1=0,
                    ratings_2=0,
                    ratings_3=0,
                    ratings_4=0,
                    ratings_5=0,
                )
                db.add(metric)
            
            # Update totals
            metric.total_queries += 1
            metric.avg_response_time = (
                (metric.avg_response_time * (metric.total_queries - 1) + response_time_ms)
                / metric.total_queries
            )
            
            # Update rating distribution
            if rating == 5:
                metric.ratings_5 += 1
            elif rating == 4:
                metric.ratings_4 += 1
            elif rating == 3:
                metric.ratings_3 += 1
            elif rating == 2:
                metric.ratings_2 += 1
            elif rating == 1:
                metric.ratings_1 += 1
            
            # Calculate average rating
            total_ratings = (metric.ratings_5 + metric.ratings_4 + metric.ratings_3 + 
                           metric.ratings_2 + metric.ratings_1)
            if total_ratings > 0:
                metric.avg_rating = (
                    (metric.ratings_5 * 5 + metric.ratings_4 * 4 + metric.ratings_3 * 3 +
                     metric.ratings_2 * 2 + metric.ratings_1 * 1) / total_ratings
                )
            
            # Update cache stats
            if cache_hit:
                metric.cache_hits += 1
            else:
                metric.cache_misses += 1
            
            metric.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Recorded metric: {topic} | Rating: {rating}⭐ | Time: {response_time_ms}ms")
            return metric.to_dict()
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
            db.rollback()
            return {}
        finally:
            db.close()
    
    def get_optimization_insights(self) -> List[Dict]:
        """Analyze metrics and generate optimization recommendations."""
        db = SessionLocal()
        try:
            insights = []
            
            # Find topics with low average ratings
            low_rating_metrics = db.query(PerformanceMetric).filter(
                PerformanceMetric.avg_rating < 3.0
            ).order_by(PerformanceMetric.avg_rating).limit(5).all()
            
            for metric in low_rating_metrics:
                insight = OptimizationInsight(
                    id=str(uuid.uuid4()),
                    category="performance",
                    title=f"Low Rating Alert: {metric.topic}",
                    description=f"Topic '{metric.topic}' has average rating of {metric.avg_rating:.1f}⭐",
                    recommendation=f"Review and improve answers about '{metric.topic}'. Consider query rewriting.",
                    affected_users=1,
                    priority="high",
                )
                insights.append(insight.to_dict())
            
            # Find topics with high response times
            slow_metrics = db.query(PerformanceMetric).filter(
                PerformanceMetric.avg_response_time > 5000
            ).order_by(PerformanceMetric.avg_response_time.desc()).limit(5).all()
            
            for metric in slow_metrics:
                insight = OptimizationInsight(
                    id=str(uuid.uuid4()),
                    category="performance",
                    title=f"Slow Response: {metric.topic}",
                    description=f"Topic '{metric.topic}' has avg response time {metric.avg_response_time:.0f}ms",
                    recommendation=f"Increase cache size or optimize retrieval for '{metric.topic}'",
                    affected_users=1,
                    potential_improvement="20% faster responses",
                    priority="medium",
                )
                insights.append(insight.to_dict())
            
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
        finally:
            db.close()
    
    def get_topic_analysis(self, topic: str = "general") -> Dict:
        """Analyze performance for a specific topic."""
        db = SessionLocal()
        try:
            metrics = db.query(PerformanceMetric).filter_by(topic=topic).all()
            
            if not metrics:
                return {"topic": topic, "data_points": 0}
            
            total_queries = sum([m.total_queries for m in metrics])
            avg_response_time = sum([m.avg_response_time for m in metrics]) / len(metrics)
            avg_rating = sum([m.avg_rating for m in metrics]) / len(metrics)
            total_cache_hits = sum([m.cache_hits for m in metrics])
            total_cache_misses = sum([m.cache_misses for m in metrics])
            
            return {
                "topic": topic,
                "data_points": len(metrics),
                "total_queries": total_queries,
                "avg_response_time_ms": round(avg_response_time, 2),
                "avg_rating": round(avg_rating, 2),
                "cache_hit_rate": round(
                    (total_cache_hits / (total_cache_hits + total_cache_misses) * 100) 
                    if (total_cache_hits + total_cache_misses) > 0 else 0, 
                    2
                ),
            }
        finally:
            db.close()


# ─── Main Adaptive Learning Manager ────────────────────────────────────────────

class AdaptiveLearningManager:
    """Orchestrate all adaptive learning components."""
    
    def __init__(self):
        self.query_rewriter = QueryRewriter()
        self.user_profiles = UserProfileManager()
        self.query_clustering = QueryClusteringEngine()
        self.cache_engine = self.query_clustering  # Alias for backward compat
        self.performance_metrics = PerformanceMetrics()
        self.metrics = self.performance_metrics  # Alias for backward compat
    
    def process_interaction(self, user_id: str, query: str, answer: str, rating: int,
                           sources: List = None, topic: str = "general",
                           response_time_ms: int = 0, cached: bool = False) -> Dict:
        """
        Process a complete user interaction and update all learning components.
        
        This is the main entry point for the learning system.
        """
        if sources is None:
            sources = []
        
        feedback_id = str(uuid.uuid4())
        
        db = SessionLocal()
        try:
            # 1. Record feedback
            feedback = Feedback(
                id=feedback_id,
                user_id=user_id,
                query=query,
                answer=answer,
                rating=rating,
                sources=sources,
                topic=topic,
                response_time_ms=response_time_ms,
            )
            db.add(feedback)
            
            # 2. Update user profile
            self.user_profiles.update_user_profile(user_id, topic, rating, response_time_ms, sources)
            
            # 3. Cache high-quality answers
            if rating >= 4:
                self.query_clustering.cache_query(query, answer, rating, sources, topic, user_id, response_time_ms)
            
            # 4. Record metrics
            self.performance_metrics.record_interaction(topic, rating, response_time_ms, cache_hit=cached)
            
            # 5. Suggest query rewrite for poor ratings
            if rating <= 2:
                rewrite_suggestion = self.query_rewriter.suggest_rewrite(query)
                if rewrite_suggestion:
                    logger.warning(f"Low rating ({rating}⭐) - Suggesting rewrite: {rewrite_suggestion}")
            
            db.commit()
            
            logger.info(f"✓ Processed interaction: {user_id} | {topic} | Rating: {rating}⭐")
            
            return {
                "feedback_id": feedback_id,
                "processed": True,
                "learning_updates": {
                    "profile_updated": True,
                    "cached": rating >= 4,
                    "metrics_recorded": True,
                }
            }
        except Exception as e:
            logger.error(f"Error processing interaction: {e}")
            db.rollback()
            return {"processed": False, "error": str(e)}
        finally:
            db.close()
    
    def get_dashboard_stats(self) -> Dict:
        """Get all learning statistics for dashboard."""
        db = SessionLocal()
        try:
            # Count totals
            total_feedback = db.query(Feedback).count()
            total_users = db.query(UserProfile).count()
            total_cached = db.query(QueryCache).count()
            
            # Calculate averages
            if total_feedback > 0:
                avg_feedback_rating = db.query(Feedback).with_entities(
                    Feedback.rating
                ).all()
                avg_rating = sum([r[0] for r in avg_feedback_rating]) / len(avg_feedback_rating)
            else:
                avg_rating = 0.0
            
            # Calculate system health
            system_health = min(100, int(avg_rating * 20)) if avg_rating > 0 else 0
            
            # Cache hit rate
            total_metrics = db.query(PerformanceMetric).all()
            total_hits = sum([m.cache_hits for m in total_metrics])
            total_misses = sum([m.cache_misses for m in total_metrics])
            cache_hit_rate = (total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0
            
            return {
                "system_health": system_health,
                "average_rating": round(avg_rating, 1),
                "total_feedback": total_feedback,
                "total_users": total_users,
                "total_cached_queries": total_cached,
                "cache_hit_rate": round(cache_hit_rate, 1),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
        finally:
            db.close()
    
    def get_learning_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive learning dashboard data."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_stats": self.get_dashboard_stats(),
            "user_stats": self.user_profiles.get_all_user_stats(),
            "cache_stats": self.query_clustering.get_cache_stats(),
            "performance_insights": self.performance_metrics.get_optimization_insights(),
        }
    
    def suggest_improvements(self, query: str) -> Dict[str, Any]:
        """Suggest query improvements and alternatives."""
        return {
            "original_query": query,
            "rewrite_suggestion": self.query_rewriter.suggest_rewrite(query),
            "similar_cached": self.query_clustering.find_similar_cached(query),
        }


# ─── Global Instance ──────────────────────────────────────────────────────────

adaptive_manager = AdaptiveLearningManager()
