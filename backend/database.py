"""
PostgreSQL Database Models and Connection
Using SQLAlchemy ORM for type safety and migrations
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Database Models ──────────────────────────────────────────────────────────

class UserProfile(Base):
    """User preference and interaction history."""
    __tablename__ = "user_profiles"
    
    id = Column(String(255), primary_key=True)  # user_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User preferences
    common_topics = Column(JSON, default={})  # {"topic": count, ...}
    preferred_sources = Column(JSON, default={})  # {"source": count, ...}
    avg_rating = Column(Float, default=0.0)
    total_interactions = Column(Integer, default=0)
    
    # Adaptive RAG parameters
    top_k = Column(Integer, default=5)
    similarity_threshold = Column(Float, default=0.7)
    use_cache = Column(Boolean, default=True)
    
    # Profile metadata
    metadata_ = Column(JSON, default={})
    
    __table_args__ = (
        Index("idx_user_created", "created_at"),
        Index("idx_user_updated", "updated_at"),
    )
    
    def to_dict(self):
        return {
            "user_id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "common_topics": self.common_topics,
            "preferred_sources": self.preferred_sources,
            "avg_rating": self.avg_rating,
            "total_interactions": self.total_interactions,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "use_cache": self.use_cache,
        }


class QueryCache(Base):
    """Cached high-quality query-answer pairs."""
    __tablename__ = "query_cache"
    
    id = Column(String(255), primary_key=True)  # hash(query)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Query and answer
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, default=[])  # List of source references
    
    # Quality metrics
    rating = Column(Integer, default=5)  # 1-5
    hit_count = Column(Integer, default=0)  # Times retrieved from cache
    avg_rating = Column(Float, default=5.0)  # Average of all ratings
    
    # Metadata
    topic = Column(String(255), default="general")
    user_id = Column(String(255), nullable=True)  # NULL = global cache
    generation_time_ms = Column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_cache_created", "created_at"),
        Index("idx_cache_topic", "topic"),
        Index("idx_cache_user_id", "user_id"),
        Index("idx_cache_rating", "rating"),
    )
    
    def to_dict(self):
        return {
            "query_hash": self.id,
            "query": self.query,
            "answer": self.answer,
            "sources": self.sources,
            "rating": self.rating,
            "hit_count": self.hit_count,
            "avg_rating": self.avg_rating,
            "topic": self.topic,
            "user_id": self.user_id,
            "generation_time_ms": self.generation_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }


class PerformanceMetric(Base):
    """Per-topic performance tracking."""
    __tablename__ = "performance_metrics"
    
    id = Column(String(255), primary_key=True)  # f"{topic}_{datetime.now().date()}"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Topic tracking
    topic = Column(String(255), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    
    # Metrics
    total_queries = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    
    # Per-rating distribution
    ratings_5 = Column(Integer, default=0)
    ratings_4 = Column(Integer, default=0)
    ratings_3 = Column(Integer, default=0)
    ratings_2 = Column(Integer, default=0)
    ratings_1 = Column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_metric_topic", "topic"),
        Index("idx_metric_date", "date"),
        Index("idx_metric_topic_date", "topic", "date"),
    )
    
    def to_dict(self):
        return {
            "metric_id": self.id,
            "topic": self.topic,
            "date": self.date,
            "total_queries": self.total_queries,
            "avg_response_time": self.avg_response_time,
            "avg_rating": self.avg_rating,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "rating_distribution": {
                "5": self.ratings_5,
                "4": self.ratings_4,
                "3": self.ratings_3,
                "2": self.ratings_2,
                "1": self.ratings_1,
            }
        }


class QueryRewrite(Base):
    """Query rewriting history and effectiveness."""
    __tablename__ = "query_rewrites"
    
    id = Column(String(255), primary_key=True)  # hash(original + timestamp)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Original vs rewritten
    original_query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=False)
    
    # Effectiveness
    original_rating = Column(Integer, nullable=True)
    rewritten_rating = Column(Integer, nullable=True)
    improvement = Column(Integer, default=0)  # rewritten_rating - original_rating
    successful = Column(Boolean, default=False)
    
    # Context
    user_id = Column(String(255), nullable=True)
    rewrite_strategy = Column(String(255), default="default")  # semantic, grammar, domain, etc.
    
    __table_args__ = (
        Index("idx_rewrite_created", "created_at"),
        Index("idx_rewrite_successful", "successful"),
    )
    
    def to_dict(self):
        return {
            "rewrite_id": self.id,
            "original_query": self.original_query,
            "rewritten_query": self.rewritten_query,
            "original_rating": self.original_rating,
            "rewritten_rating": self.rewritten_rating,
            "improvement": self.improvement,
            "successful": self.successful,
            "strategy": self.rewrite_strategy,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Feedback(Base):
    """User feedback on responses."""
    __tablename__ = "feedback"
    
    id = Column(String(255), primary_key=True)  # uuid
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Core feedback
    user_id = Column(String(255), nullable=True, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    
    # Metadata
    sources = Column(JSON, default=[])
    topic = Column(String(255), default="general")
    response_time_ms = Column(Integer, nullable=True)
    
    # Optional additional feedback
    comments = Column(Text, nullable=True)
    helpful = Column(Boolean, nullable=True)  # True/False/None
    
    # System context
    session_id = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index("idx_feedback_user_id", "user_id"),
        Index("idx_feedback_created", "created_at"),
        Index("idx_feedback_rating", "rating"),
        Index("idx_feedback_topic", "topic"),
    )
    
    def to_dict(self):
        return {
            "feedback_id": self.id,
            "user_id": self.user_id,
            "query": self.query,
            "answer": self.answer,
            "rating": self.rating,
            "sources": self.sources,
            "topic": self.topic,
            "response_time_ms": self.response_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OptimizationInsight(Base):
    """Auto-generated system optimization recommendations."""
    __tablename__ = "optimization_insights"
    
    id = Column(String(255), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Insight details
    category = Column(String(255), nullable=False)  # cache, performance, user_profile, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    
    # Context
    affected_users = Column(Integer, default=1)
    potential_improvement = Column(String(255), default="")  # e.g., "15% faster responses"
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Status
    implemented = Column(Boolean, default=False)
    implementation_date = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_insight_created", "created_at"),
        Index("idx_insight_category", "category"),
    )
    
    def to_dict(self):
        return {
            "insight_id": self.id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
            "affected_users": self.affected_users,
            "potential_improvement": self.potential_improvement,
            "priority": self.priority,
            "implemented": self.implemented,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def init_db():
    """Initialize database - create all tables."""
    logger.info(f"Initializing database at {DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database initialized successfully")
