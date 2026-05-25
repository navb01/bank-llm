"""
Self-Learning System for BankAssist AI
Tracks feedback, analyzes patterns, and optimizes RAG parameters.
Enables the system to improve over time based on user interactions.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
import statistics

from config import BASE_DIR, LOGS_DIR

logger = logging.getLogger(__name__)

# Learning database file
LEARNING_DB_FILE = BASE_DIR / "learning" / "feedback.jsonl"
LEARNING_DB_FILE.parent.mkdir(exist_ok=True, parents=True)

STATS_FILE = BASE_DIR / "learning" / "stats.json"
INSIGHTS_FILE = BASE_DIR / "learning" / "insights.json"


# ─── Feedback Storage ─────────────────────────────────────────────────────────

class FeedbackStore:
    """Store and retrieve user feedback on answers."""
    
    def __init__(self):
        self.db_file = LEARNING_DB_FILE
        self.ensure_file()
    
    def ensure_file(self):
        """Create database file if not exists."""
        if not self.db_file.exists():
            self.db_file.touch()
    
    def add_feedback(self, query: str, answer: str, rating: int, sources: list, 
                    user_comment: str = "", user_ip: str = "unknown") -> Dict:
        """
        Record user feedback on an answer.
        
        Args:
            query: Original user query
            answer: AI-generated answer
            rating: 1-5 (1=bad, 3=neutral, 5=excellent)
            sources: List of source documents
            user_comment: Optional user comment
            user_ip: User IP address
        
        Returns:
            Feedback record
        """
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer[:500],  # Store first 500 chars
            "rating": max(1, min(5, rating)),  # Clamp 1-5
            "sources": sources,
            "comment": user_comment[:200],  # First 200 chars
            "user_ip": user_ip,
        }
        
        # Append to file
        with open(self.db_file, "a") as f:
            f.write(json.dumps(feedback) + "\n")
        
        logger.info(f"Feedback recorded: query={query[:50]}... rating={rating}")
        return feedback
    
    def get_recent_feedback(self, hours: int = 24) -> List[Dict]:
        """Get feedback from last N hours."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        feedback = []
        
        try:
            with open(self.db_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    fb = json.loads(line)
                    if fb["timestamp"] >= cutoff:
                        feedback.append(fb)
        except Exception as e:
            logger.error(f"Error reading feedback: {e}")
        
        return feedback
    
    def get_all_feedback(self) -> List[Dict]:
        """Get all feedback records."""
        feedback = []
        try:
            with open(self.db_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    feedback.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error reading feedback: {e}")
        
        return feedback


# ─── Analytics ────────────────────────────────────────────────────────────────

class Analytics:
    """Analyze user interactions and system performance."""
    
    def __init__(self):
        self.feedback_store = FeedbackStore()
    
    def compute_stats(self) -> Dict[str, Any]:
        """Compute learning statistics."""
        feedback = self.feedback_store.get_all_feedback()
        
        if not feedback:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "common_topics": [],
                "answer_quality": "No data yet",
                "learning_status": "Initializing"
            }
        
        ratings = [fb["rating"] for fb in feedback]
        queries = [fb["query"] for fb in feedback]
        
        # Compute metrics
        avg_rating = statistics.mean(ratings)
        rating_dist = Counter(ratings)
        
        # Extract common topics from queries
        stop_words = {"what", "is", "the", "a", "are", "how", "can", "show", "me", "about"}
        words = []
        for q in queries:
            words.extend([w.lower() for w in q.split() if len(w) > 3 and w.lower() not in stop_words])
        common_words = Counter(words).most_common(5)
        
        # Quality assessment
        if avg_rating >= 4.5:
            quality = "Excellent"
        elif avg_rating >= 4.0:
            quality = "Very Good"
        elif avg_rating >= 3.5:
            quality = "Good"
        elif avg_rating >= 3.0:
            quality = "Fair"
        else:
            quality = "Needs Improvement"
        
        stats = {
            "total_feedback": len(feedback),
            "average_rating": round(avg_rating, 2),
            "rating_1_count": rating_dist.get(1, 0),
            "rating_2_count": rating_dist.get(2, 0),
            "rating_3_count": rating_dist.get(3, 0),
            "rating_4_count": rating_dist.get(4, 0),
            "rating_5_count": rating_dist.get(5, 0),
            "common_topics": [{"word": w, "count": c} for w, c in common_words],
            "answer_quality": quality,
            "learning_status": "Active Learning" if len(feedback) > 10 else "Gathering Feedback",
            "last_updated": datetime.now().isoformat(),
        }
        
        # Save to file
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save stats: {e}")
        
        return stats
    
    def get_improvement_recommendations(self) -> List[str]:
        """Get recommendations for improving the system."""
        feedback = self.feedback_store.get_all_feedback()
        stats = self.compute_stats()
        
        recommendations = []
        
        if not feedback:
            return ["Start using the system to generate learning insights"]
        
        avg_rating = stats.get("average_rating", 0)
        total = stats.get("total_feedback", 0)
        
        # Low ratings
        low_ratings = stats.get("rating_1_count", 0) + stats.get("rating_2_count", 0)
        if low_ratings > total * 0.2:
            recommendations.append(f"⚠️ {low_ratings} low ratings detected. Consider uploading more relevant circulars or adjusting RAG parameters.")
        
        # Quality assessment
        if avg_rating < 3.5:
            recommendations.append("📚 Answer quality is below 3.5/5. Upload additional circulars or improve document indexing.")
            recommendations.append("🔍 Consider lowering MIN_SIMILARITY_SCORE in config.py to surface more documents.")
        
        if avg_rating < 3.0:
            recommendations.append("🛠️ System needs calibration. Review recent low-rated answers and adjust chunk sizes.")
        
        # Positive feedback
        if avg_rating >= 4.0:
            recommendations.append("✅ System is performing well! Continue monitoring for edge cases.")
        
        # Data collection
        if total < 20:
            recommendations.append("📊 Need more feedback data. Continue using the system to improve learning.")
        elif total < 50:
            recommendations.append("📈 Learning in progress. We recommend ~100 feedback samples for reliable insights.")
        
        # Common topics
        topics = stats.get("common_topics", [])
        if topics:
            top_topic = topics[0].get("word", "").lower()
            recommendations.append(f"📌 Most common topic: '{top_topic}'. Ensure you have comprehensive circulars on this topic.")
        
        return recommendations if recommendations else ["System is optimized. Keep monitoring performance."]
    
    def get_performance_by_source(self) -> Dict[str, Dict]:
        """Analyze which sources get best ratings."""
        feedback = self.feedback_store.get_all_feedback()
        source_stats = defaultdict(list)
        
        for fb in feedback:
            for source in fb.get("sources", []):
                source_name = source.get("filename", "unknown")
                source_stats[source_name].append(fb["rating"])
        
        result = {}
        for source, ratings in source_stats.items():
            result[source] = {
                "count": len(ratings),
                "avg_rating": round(statistics.mean(ratings), 2),
                "max_rating": max(ratings),
                "min_rating": min(ratings),
            }
        
        return dict(sorted(result.items(), key=lambda x: x[1]["avg_rating"], reverse=True))


# ─── Adaptive RAG ─────────────────────────────────────────────────────────────

class AdaptiveRAG:
    """Adapt RAG parameters based on learning."""
    
    def __init__(self):
        self.analytics = Analytics()
        self.insights_file = INSIGHTS_FILE
    
    def suggest_optimizations(self) -> Dict[str, Any]:
        """Suggest RAG parameter adjustments."""
        stats = self.analytics.compute_stats()
        recommendations = self.analytics.get_improvement_recommendations()
        
        avg_rating = stats.get("average_rating", 3.0)
        total = stats.get("total_feedback", 0)
        
        optimizations = {
            "timestamp": datetime.now().isoformat(),
            "current_rating": avg_rating,
            "feedback_samples": total,
            "suggested_changes": [],
            "confidence": "low" if total < 20 else "medium" if total < 50 else "high"
        }
        
        # Suggestions based on feedback
        if total >= 20:
            if avg_rating < 3.0:
                optimizations["suggested_changes"].append({
                    "parameter": "MIN_SIMILARITY_SCORE",
                    "action": "decrease",
                    "from": 0.10,
                    "to": 0.05,
                    "reason": "More documents may help answer questions"
                })
                optimizations["suggested_changes"].append({
                    "parameter": "TOP_K_RESULTS",
                    "action": "increase",
                    "from": 8,
                    "to": 12,
                    "reason": "Cast wider net to find relevant documents"
                })
            elif avg_rating > 4.0:
                optimizations["suggested_changes"].append({
                    "parameter": "MIN_SIMILARITY_SCORE",
                    "action": "increase",
                    "from": 0.10,
                    "to": 0.20,
                    "reason": "System is performing well, can be more selective"
                })
        
        optimizations["recommendations"] = recommendations
        
        # Save insights
        try:
            with open(self.insights_file, "w") as f:
                json.dump(optimizations, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save insights: {e}")
        
        return optimizations
    
    def get_current_insights(self) -> Dict[str, Any]:
        """Get current optimization insights."""
        if self.insights_file.exists():
            try:
                with open(self.insights_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not read insights: {e}")
        
        return self.suggest_optimizations()


# ─── Self-Learning Manager ────────────────────────────────────────────────────

class SelfLearningManager:
    """Main interface for all self-learning features."""
    
    def __init__(self):
        self.feedback_store = FeedbackStore()
        self.analytics = Analytics()
        self.adaptive_rag = AdaptiveRAG()
    
    def process_feedback(self, query: str, answer: str, rating: int, 
                        sources: list, comment: str = "", user_ip: str = "unknown"):
        """Record feedback and update learning."""
        self.feedback_store.add_feedback(query, answer, rating, sources, comment, user_ip)
        
        # Update stats
        self.analytics.compute_stats()
        
        # Generate insights if enough feedback
        feedback_count = len(self.feedback_store.get_all_feedback())
        if feedback_count % 5 == 0:  # Every 5 feedback items
            self.adaptive_rag.suggest_optimizations()
        
        logger.info(f"Learning updated: {feedback_count} total feedback records")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for learning dashboard."""
        return {
            "stats": self.analytics.compute_stats(),
            "recommendations": self.analytics.get_improvement_recommendations(),
            "optimizations": self.adaptive_rag.get_current_insights(),
            "source_performance": self.analytics.get_performance_by_source(),
        }
    
    def export_learning_data(self) -> str:
        """Export all learning data."""
        return json.dumps({
            "feedback": self.feedback_store.get_all_feedback(),
            "stats": self.analytics.compute_stats(),
            "insights": self.adaptive_rag.get_current_insights(),
        }, indent=2)


# Global instance
learning_manager = SelfLearningManager()


if __name__ == "__main__":
    # Test
    manager = SelfLearningManager()
    
    # Add sample feedback
    manager.process_feedback(
        query="What is the RBI repo rate?",
        answer="Based on the latest circular, the repo rate is 5.5%",
        rating=5,
        sources=[{"filename": "RBI_Circular_2024.pdf", "ref_no": "RBI/2024/001"}],
        comment="Very helpful",
        user_ip="192.168.1.100"
    )
    
    # Get dashboard
    dashboard = manager.get_dashboard_data()
    print(json.dumps(dashboard, indent=2))
