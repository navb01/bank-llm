"""
Database initialization and migration from JSON to PostgreSQL
Run this once to set up the database and migrate existing data
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import uuid
import hashlib

from database import init_db, SessionLocal, UserProfile, QueryCache, PerformanceMetric, QueryRewrite, Feedback, OptimizationInsight
from config import BASE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEARNING_DIR = BASE_DIR / "learning"


def migrate_user_profiles():
    """Migrate user profiles from JSON to database."""
    profile_file = LEARNING_DIR / "adaptive_db" / "user_profiles.json"
    
    if not profile_file.exists():
        logger.info("No user profiles to migrate")
        return
    
    db = SessionLocal()
    try:
        with open(profile_file, "r") as f:
            profiles = json.load(f)
        
        for user_id, profile_data in profiles.items():
            existing = db.query(UserProfile).filter_by(id=user_id).first()
            if existing:
                logger.info(f"User profile {user_id} already in DB, skipping")
                continue
            
            profile = UserProfile(
                id=user_id,
                common_topics=profile_data.get("common_topics", {}),
                preferred_sources=profile_data.get("preferred_sources", {}),
                avg_rating=profile_data.get("avg_rating", 0.0),
                total_interactions=profile_data.get("total_interactions", 0),
                top_k=profile_data.get("top_k", 5),
                similarity_threshold=profile_data.get("similarity_threshold", 0.7),
                use_cache=profile_data.get("use_cache", True),
            )
            db.add(profile)
            logger.info(f"✓ Migrated user profile: {user_id}")
        
        db.commit()
        logger.info("✓ User profiles migration complete")
    except Exception as e:
        logger.error(f"Error migrating user profiles: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_query_cache():
    """Migrate query cache from JSON to database."""
    cache_file = LEARNING_DIR / "adaptive_db" / "query_cache.json"
    
    if not cache_file.exists():
        logger.info("No query cache to migrate")
        return
    
    db = SessionLocal()
    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
        
        for query_hash, cache_entry in cache_data.items():
            existing = db.query(QueryCache).filter_by(id=query_hash).first()
            if existing:
                logger.info(f"Cache entry {query_hash} already in DB, skipping")
                continue
            
            cache = QueryCache(
                id=query_hash,
                query=cache_entry.get("query", ""),
                answer=cache_entry.get("answer", ""),
                sources=cache_entry.get("sources", []),
                rating=cache_entry.get("rating", 5),
                hit_count=cache_entry.get("hit_count", 0),
                avg_rating=cache_entry.get("avg_rating", 5.0),
                topic=cache_entry.get("topic", "general"),
                user_id=cache_entry.get("user_id", None),
                generation_time_ms=cache_entry.get("generation_time_ms", 0),
            )
            db.add(cache)
            logger.info(f"✓ Migrated cache entry: {query_hash[:16]}...")
        
        db.commit()
        logger.info("✓ Query cache migration complete")
    except Exception as e:
        logger.error(f"Error migrating query cache: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_performance_metrics():
    """Migrate performance metrics from JSON to database."""
    metrics_file = LEARNING_DIR / "adaptive_db" / "performance_metrics.json"
    
    if not metrics_file.exists():
        logger.info("No performance metrics to migrate")
        return
    
    db = SessionLocal()
    try:
        with open(metrics_file, "r") as f:
            metrics_data = json.load(f)
        
        for metric_id, metric_entry in metrics_data.items():
            existing = db.query(PerformanceMetric).filter_by(id=metric_id).first()
            if existing:
                logger.info(f"Metric {metric_id} already in DB, skipping")
                continue
            
            rating_dist = metric_entry.get("rating_distribution", {})
            metric = PerformanceMetric(
                id=metric_id,
                topic=metric_entry.get("topic", "general"),
                date=metric_entry.get("date", ""),
                total_queries=metric_entry.get("total_queries", 0),
                avg_response_time=metric_entry.get("avg_response_time", 0.0),
                avg_rating=metric_entry.get("avg_rating", 0.0),
                cache_hits=metric_entry.get("cache_hits", 0),
                cache_misses=metric_entry.get("cache_misses", 0),
                ratings_5=rating_dist.get("5", 0),
                ratings_4=rating_dist.get("4", 0),
                ratings_3=rating_dist.get("3", 0),
                ratings_2=rating_dist.get("2", 0),
                ratings_1=rating_dist.get("1", 0),
            )
            db.add(metric)
            logger.info(f"✓ Migrated metric: {metric_id}")
        
        db.commit()
        logger.info("✓ Performance metrics migration complete")
    except Exception as e:
        logger.error(f"Error migrating performance metrics: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_query_rewrites():
    """Migrate query rewrites from JSONL to database."""
    rewrites_file = LEARNING_DIR / "adaptive_db" / "query_rewrites.jsonl"
    
    if not rewrites_file.exists():
        logger.info("No query rewrites to migrate")
        return
    
    db = SessionLocal()
    try:
        with open(rewrites_file, "r") as f:
            for line in f:
                rewrite_data = json.loads(line)
                rewrite_id = hashlib.md5(
                    f"{rewrite_data['original_query']}{rewrite_data['timestamp']}".encode()
                ).hexdigest()
                
                existing = db.query(QueryRewrite).filter_by(id=rewrite_id).first()
                if existing:
                    continue
                
                rewrite = QueryRewrite(
                    id=rewrite_id,
                    original_query=rewrite_data.get("original_query", ""),
                    rewritten_query=rewrite_data.get("rewritten_query", ""),
                    original_rating=rewrite_data.get("original_rating"),
                    rewritten_rating=rewrite_data.get("rewritten_rating"),
                    improvement=rewrite_data.get("improvement", 0),
                    successful=rewrite_data.get("successful", False),
                )
                db.add(rewrite)
        
        db.commit()
        logger.info("✓ Query rewrites migration complete")
    except Exception as e:
        logger.error(f"Error migrating query rewrites: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_feedback():
    """Migrate feedback from JSONL to database."""
    feedback_file = LEARNING_DIR / "feedback.jsonl"
    
    if not feedback_file.exists():
        logger.info("No feedback to migrate")
        return
    
    db = SessionLocal()
    try:
        with open(feedback_file, "r") as f:
            for line in f:
                feedback_data = json.loads(line)
                feedback_id = str(uuid.uuid4())
                
                feedback = Feedback(
                    id=feedback_id,
                    user_id=feedback_data.get("user_id"),
                    query=feedback_data.get("query", ""),
                    answer=feedback_data.get("answer", ""),
                    rating=feedback_data.get("rating", 3),
                    sources=feedback_data.get("sources", []),
                    topic=feedback_data.get("topic", "general"),
                    response_time_ms=feedback_data.get("response_time_ms"),
                )
                db.add(feedback)
        
        db.commit()
        logger.info("✓ Feedback migration complete")
    except Exception as e:
        logger.error(f"Error migrating feedback: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Run all migrations."""
    logger.info("=" * 70)
    logger.info("Starting database initialization and migration")
    logger.info("=" * 70)
    
    # Initialize database
    init_db()
    
    # Migrate data from JSON files
    logger.info("\nMigrating existing data from JSON to database...")
    migrate_user_profiles()
    migrate_query_cache()
    migrate_performance_metrics()
    migrate_query_rewrites()
    migrate_feedback()
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ Database migration complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
