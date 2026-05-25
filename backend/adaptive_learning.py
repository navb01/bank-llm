"""
Advanced Adaptive Learning System for Bank LLM
- Query rewriting based on poor performance
- User profile learning and personalization
- Semantic query clustering for pattern recognition
- Adaptive retrieval parameters per user/domain
- Answer quality prediction and ranking
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics
import hashlib
from difflib import SequenceMatcher

from config import BASE_DIR

logger = logging.getLogger(__name__)

ADAPTIVE_DB = BASE_DIR / "learning" / "adaptive_db"
ADAPTIVE_DB.mkdir(exist_ok=True, parents=True)

QUERY_CLUSTERS_FILE = ADAPTIVE_DB / "query_clusters.json"
USER_PROFILES_FILE = ADAPTIVE_DB / "user_profiles.json"
QUERY_CACHE_FILE = ADAPTIVE_DB / "query_cache.json"
PERFORMANCE_METRICS_FILE = ADAPTIVE_DB / "performance_metrics.json"


# ─── Query Rewriting ──────────────────────────────────────────────────────────

class QueryRewriter:
    """Learn from poor-performing queries and suggest improvements."""
    
    def __init__(self):
        self.rewrite_history_file = ADAPTIVE_DB / "query_rewrites.jsonl"
        self.ensure_file()
    
    def ensure_file(self):
        """Create rewrite history file if not exists."""
        if not self.rewrite_history_file.exists():
            self.rewrite_history_file.touch()
    
    def record_rewrite(self, original: str, rewritten: str, original_rating: int, 
                      rewritten_rating: int) -> Dict:
        """Record a successful or failed query rewrite."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "original_query": original,
            "rewritten_query": rewritten,
            "original_rating": original_rating,
            "rewritten_rating": rewritten_rating,
            "improvement": rewritten_rating - original_rating,
            "successful": rewritten_rating > original_rating,
        }
        
        with open(self.rewrite_history_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        
        return record
    
    def suggest_rewrite(self, query: str, low_rating: bool = True) -> Optional[str]:
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
                # Check if alternatives would improve specificity
                return f"{query} (regulatory reference)"
        
        # Strategy 2: If query is very long, break it down
        if len(query) > 150:
            # Try shortening by removing modifiers
            words = query.split()
            if len(words) > 20:
                core_query = " ".join(words[:15])  # First 15 words
                return f"{core_query}?"
        
        # Strategy 3: Add regulatory authority if missing
        if not any(auth in query_lower for auth in ["rbi", "sebi", "nabard", "dfs"]):
            if "rate" in query_lower or "policy" in query_lower:
                return f"{query} (RBI guideline)"
            elif "securities" in query_lower or "market" in query_lower:
                return f"{query} (SEBI regulation)"
        
        # Strategy 4: Simplify if contains "how" and "why"
        if "how" in query_lower and "why" in query_lower:
            # Split into two simpler questions
            how_part = query.replace("why", "").replace("How", "").strip()
            return f"How {how_part}"
        
        return None  # No rewrite suggested
    
    def get_best_rewrites(self, limit: int = 5) -> List[Dict]:
        """Get most successful rewrites."""
        rewrites = []
        try:
            with open(self.rewrite_history_file, "r") as f:
                for line in f:
                    if line.strip():
                        rewrites.append(json.loads(line))
        except Exception as e:
            logger.warning(f"Error reading rewrites: {e}")
        
        # Filter successful ones and sort by improvement
        successful = [r for r in rewrites if r.get("successful")]
        successful.sort(key=lambda x: x.get("improvement", 0), reverse=True)
        
        return successful[:limit]


# ─── User Profile Learning ────────────────────────────────────────────────────

class UserProfileManager:
    """Learn individual user preferences and patterns."""
    
    def __init__(self):
        self.profiles_file = USER_PROFILES_FILE
        self.load_profiles()
    
    def load_profiles(self) -> Dict[str, Dict]:
        """Load all user profiles."""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r") as f:
                    self.profiles = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading profiles: {e}")
                self.profiles = {}
        else:
            self.profiles = {}
        
        return self.profiles
    
    def save_profiles(self):
        """Save user profiles."""
        try:
            with open(self.profiles_file, "w") as f:
                json.dump(self.profiles, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving profiles: {e}")
    
    def update_user_profile(self, user_id: str, query: str, rating: int, 
                          sources: list, response_time: float = 0):
        """Update user profile based on interaction."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "first_seen": datetime.now().isoformat(),
                "total_queries": 0,
                "avg_rating": 0,
                "rating_history": [],
                "common_topics": [],
                "preferred_sources": [],
                "query_patterns": [],
                "avg_response_time": 0,
            }
        
        profile = self.profiles[user_id]
        
        # Update basic stats
        profile["total_queries"] += 1
        profile["last_query"] = datetime.now().isoformat()
        profile["rating_history"].append(rating)
        profile["avg_rating"] = statistics.mean(profile["rating_history"][-20:])  # Last 20
        
        # Extract and track topics (first 2-3 words)
        topic = " ".join(query.split()[:3]).lower()
        profile["query_patterns"].append(topic)
        common = Counter(profile["query_patterns"]).most_common(5)
        profile["common_topics"] = [{"topic": t, "count": c} for t, c in common]
        
        # Track preferred sources
        for source in sources:
            profile["preferred_sources"].append(source.get("filename", "unknown"))
        source_counts = Counter(profile["preferred_sources"]).most_common(3)
        profile["preferred_sources"] = [{"name": s, "count": c} for s, c in source_counts]
        
        # Response time average
        if response_time > 0:
            profile["response_times"] = profile.get("response_times", []) + [response_time]
            profile["avg_response_time"] = statistics.mean(profile["response_times"][-50:])
        
        self.save_profiles()
        return profile
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile."""
        self.load_profiles()
        return self.profiles.get(user_id, {})
    
    def get_personalized_params(self, user_id: str) -> Dict:
        """Get RAG parameters tailored to user."""
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return {}  # Use defaults
        
        params = {}
        
        # Adjust TOP_K based on user rating history
        if profile.get("avg_rating", 3) > 4.0:
            params["top_k"] = 6  # They like concise results
        elif profile.get("avg_rating", 3) < 3.0:
            params["top_k"] = 12  # They may need more context
        
        # Adjust temperature based on query patterns
        if "procedure" in str(profile.get("query_patterns", [])):
            params["temperature"] = 0.05  # Very factual for procedures
        elif "definition" in str(profile.get("query_patterns", [])):
            params["temperature"] = 0.1  # Factual for definitions
        
        return params
    
    def get_all_user_stats(self) -> Dict:
        """Get statistics across all users."""
        self.load_profiles()
        
        if not self.profiles:
            return {"total_users": 0, "avg_rating_all_users": 0}
        
        ratings = []
        for profile in self.profiles.values():
            ratings.extend(profile.get("rating_history", []))
        
        return {
            "total_users": len(self.profiles),
            "total_interactions": sum(p.get("total_queries", 0) for p in self.profiles.values()),
            "avg_rating_all_users": round(statistics.mean(ratings), 2) if ratings else 0,
            "active_users_24h": sum(
                1 for p in self.profiles.values()
                if datetime.fromisoformat(p.get("last_query", "2000-01-01")) 
                > datetime.now() - timedelta(hours=24)
            ),
        }


# ─── Query Cache and Clustering ────────────────────────────────────────────────

class QueryClusteringEngine:
    """Group similar queries and cache high-quality answers."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.cache_file = QUERY_CACHE_FILE
        self.clusters_file = QUERY_CLUSTERS_FILE
        self.threshold = similarity_threshold
        self.load_cache()
    
    def load_cache(self):
        """Load query cache."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}
    
    def save_cache(self):
        """Save query cache."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    def query_similarity(self, q1: str, q2: str) -> float:
        """Calculate similarity between two queries (0-1)."""
        return SequenceMatcher(None, q1.lower(), q2.lower()).ratio()
    
    def cache_query(self, query: str, answer: str, rating: int, sources: list):
        """Cache a high-quality query-answer pair."""
        if rating < 4:  # Only cache high-quality answers
            return
        
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        
        self.cache[query_hash] = {
            "query": query,
            "answer": answer,
            "rating": rating,
            "sources": sources,
            "cached_at": datetime.now().isoformat(),
            "access_count": 0,
        }
        
        self.save_cache()
        logger.info(f"Cached high-quality query: {query[:50]}...")
    
    def find_similar_cached(self, query: str) -> Optional[Dict]:
        """Find similar cached query-answer pair."""
        best_match = None
        best_similarity = 0
        
        for cached_entry in self.cache.values():
            sim = self.query_similarity(query, cached_entry["query"])
            if sim > best_similarity and sim >= self.threshold:
                best_similarity = sim
                best_match = cached_entry
        
        if best_match:
            best_match["access_count"] += 1
            self.save_cache()
            logger.info(f"Found cached answer with {best_similarity:.2%} similarity")
        
        return best_match
    
    def get_cache_stats(self) -> Dict:
        """Get caching statistics."""
        total_cached = len(self.cache)
        total_accesses = sum(e.get("access_count", 0) for e in self.cache.values())
        
        return {
            "total_cached_queries": total_cached,
            "total_cache_hits": total_accesses,
            "hit_rate": round((total_accesses / max(total_cached, 1)) * 100, 2),
            "avg_hits_per_query": round(total_accesses / max(total_cached, 1), 2),
        }


# ─── Performance Metrics Tracker ───────────────────────────────────────────────

class PerformanceMetrics:
    """Track detailed performance metrics for continuous optimization."""
    
    def __init__(self):
        self.metrics_file = PERFORMANCE_METRICS_FILE
        self.load_metrics()
    
    def load_metrics(self):
        """Load performance metrics."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    self.metrics = json.load(f)
            except:
                self.metrics = defaultdict(list)
        else:
            self.metrics = defaultdict(list)
    
    def save_metrics(self):
        """Save metrics."""
        try:
            with open(self.metrics_file, "w") as f:
                json.dump(dict(self.metrics), f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving metrics: {e}")
    
    def record_interaction(self, query: str, rating: int, response_time: float, 
                          chunks_found: int, source_count: int, topic: str = ""):
        """Record an interaction with full metrics."""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "rating": rating,
            "response_time_ms": response_time,
            "chunks_found": chunks_found,
            "sources_used": source_count,
            "topic": topic or "general",
        }
        
        # Store by topic
        if topic not in self.metrics:
            self.metrics[topic] = []
        self.metrics[topic].append(metric)
        
        # Keep only last 1000 per topic
        if len(self.metrics[topic]) > 1000:
            self.metrics[topic] = self.metrics[topic][-1000:]
        
        self.save_metrics()
    
    def get_topic_analysis(self, topic: str = "general") -> Dict:
        """Analyze performance for a specific topic."""
        if topic not in self.metrics or not self.metrics[topic]:
            return {"topic": topic, "data_points": 0}
        
        metrics = self.metrics[topic]
        ratings = [m["rating"] for m in metrics]
        times = [m["response_time_ms"] for m in metrics]
        chunks = [m["chunks_found"] for m in metrics]
        
        return {
            "topic": topic,
            "data_points": len(metrics),
            "avg_rating": round(statistics.mean(ratings), 2),
            "avg_response_time_ms": round(statistics.mean(times), 2),
            "avg_chunks_found": round(statistics.mean(chunks), 2),
            "rating_trend": "improving" if ratings[-5:] and statistics.mean(ratings[-5:]) > statistics.mean(ratings[:-5]) else "stable",
        }
    
    def get_optimization_insights(self) -> List[Dict]:
        """Generate insights for system optimization."""
        insights = []
        
        for topic, metrics in self.metrics.items():
            if len(metrics) < 5:
                continue
            
            recent_ratings = [m["rating"] for m in metrics[-5:]]
            older_ratings = [m["rating"] for m in metrics[:-5]]
            
            # Detect declining performance
            if recent_ratings and older_ratings:
                recent_avg = statistics.mean(recent_ratings)
                older_avg = statistics.mean(older_ratings)
                
                if recent_avg < older_avg - 0.5:
                    insights.append({
                        "type": "performance_decline",
                        "topic": topic,
                        "severity": "high" if recent_avg < 3.0 else "medium",
                        "message": f"Performance declining for '{topic}' queries. Recent avg: {recent_avg:.2f}, Previous: {older_avg:.2f}",
                    })
            
            # Fast responses with good ratings
            response_times = [m["response_time_ms"] for m in metrics[-10:]]
            if response_times and statistics.mean(response_times) < 500:
                recent_rating = statistics.mean([m["rating"] for m in metrics[-10:]])
                if recent_rating > 4.0:
                    insights.append({
                        "type": "high_performance",
                        "topic": topic,
                        "severity": "low",
                        "message": f"Excellent performance on '{topic}' queries. Fast and highly rated.",
                    })
        
        return insights


# ─── Main Adaptive Learning Manager ────────────────────────────────────────────

class AdaptiveLearningManager:
    """Unified manager for all adaptive learning features."""
    
    def __init__(self):
        self.query_rewriter = QueryRewriter()
        self.user_profiles = UserProfileManager()
        self.query_clustering = QueryClusteringEngine()
        self.performance_metrics = PerformanceMetrics()
    
    def process_interaction(self, user_id: str, query: str, answer: str, rating: int,
                          sources: list, response_time: float = 0, topic: str = ""):
        """Process a complete user interaction for all learning components."""
        
        # Update user profile
        self.user_profiles.update_user_profile(user_id, query, rating, sources, response_time)
        
        # Cache high-quality answers
        if rating >= 4:
            self.query_clustering.cache_query(query, answer, rating, sources)
        
        # Record performance metrics
        self.performance_metrics.record_interaction(
            query, rating, response_time, 
            len(sources), len(sources), topic
        )
        
        logger.info(f"Adaptive learning updated for user {user_id}: rating={rating}")
    
    def get_learning_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive learning dashboard data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "user_stats": self.user_profiles.get_all_user_stats(),
            "cache_stats": self.query_clustering.get_cache_stats(),
            "performance_insights": self.performance_metrics.get_optimization_insights(),
            "best_rewrites": self.query_rewriter.get_best_rewrites(3),
        }
    
    def suggest_improvements(self, query: str) -> Dict[str, Any]:
        """Suggest query improvements and alternatives."""
        return {
            "original_query": query,
            "rewrite_suggestion": self.query_rewriter.suggest_rewrite(query),
            "similar_cached": self.query_clustering.find_similar_cached(query),
        }


# Global instance
adaptive_manager = AdaptiveLearningManager()
