# 🧠 BankAssist AI — Self-Learning System

> Your LLM that gets smarter with every interaction. The system continuously learns from user feedback and adapts to provide better answers over time.

---

## ✨ What's New

Your Bank LLM system now includes **advanced adaptive learning capabilities** that make it smarter with every use:

### 🎯 Core Learning Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **User Profiling** | Tracks individual user preferences, query patterns, and feedback | Personalized answers tailored to each user |
| **Query Clustering** | Groups similar queries and caches high-quality answers | Faster responses for common questions |
| **Performance Tracking** | Monitors answer quality by topic and time | Identifies areas needing improvement |
| **Adaptive Parameters** | Adjusts RAG settings based on performance | Continuously optimizes retrieval |
| **Query Rewriting** | Learns to improve poorly-performing queries | Better answers for ambiguous questions |
| **User Preferences** | Learns response style preferences per user | More relevant answers over time |

---

## 📊 Learning Dashboard

Access the comprehensive learning dashboard at **`/learning`** (or click 🧠 Learning in the sidebar).

### Dashboard Tabs

#### 1. **Overview** 📊
- System health score (0-100%)
- Average answer rating
- Total feedback collected
- Key performance metrics
- Top query topics

#### 2. **User Analytics** 👥
- Total users tracked
- Total interactions
- Active users in last 24 hours
- Cross-user average rating
- User profile statistics

#### 3. **Performance** ⚡
- Query performance by topic
- Response time analytics
- Performance decline detection
- High-performance query identification

#### 4. **Insights** 💡
- System optimization recommendations
- Improvement suggestions based on feedback
- Parameter adjustment recommendations
- Data quality insights

#### 5. **Query Cache** ⚙️
- Cached queries count
- Cache hit statistics
- Hit rate percentage
- Average hits per cached query

---

## 🔄 How Learning Works

### 1. **Feedback Collection**
After each answer, users can provide immediate feedback:
- 👎 **Thumbs Down** (Rating: 1) — Not helpful
- 😐 **Neutral** (Rating: 3) — Adequate
- 👍 **Thumbs Up** (Rating: 5) — Very helpful

```
User clicks feedback button → System records interaction
→ Processes for learning → Updates profiles & metrics
```

### 2. **User Profile Learning**
The system builds individual profiles tracking:
- **Query Patterns** — Common topics and question types
- **Preferred Sources** — Which documents they rely on most
- **Rating History** — Quality expectations
- **Response Times** — Performance patterns
- **Personalized Parameters** — Customized RAG settings

```javascript
User Profile Structure:
{
  "user_123": {
    "total_queries": 45,
    "avg_rating": 4.2,
    "common_topics": [
      {"topic": "loan procedures", "count": 12},
      {"topic": "interest rates", "count": 8}
    ],
    "preferred_sources": [
      {"name": "RBI_Circular_2024.pdf", "count": 15}
    ],
    "avg_response_time": 350 // ms
  }
}
```

### 3. **Query Caching**
High-quality answers (4+ rating) are automatically cached:
- Future similar queries return cached answers instantly
- Improves response time dramatically
- Reduces compute load
- Cache hit rate tracked and monitored

```
Query Similarity → Find Similar Cached Query (≥85% similarity)
→ Return Cached Answer (instant) → Record Cache Hit
```

### 4. **Performance Metrics**
The system tracks detailed metrics by topic:
```
Metrics Tracked Per Interaction:
├── Query length
├── User rating (1-5)
├── Response time (ms)
├── Chunks found
├── Sources used
├── Topic category
└── Timestamp
```

### 5. **Optimization Insights**
System generates recommendations:
- **Performance Decline Detection** — Alert when scores drop
- **High-Performance Recognition** — Identify working patterns
- **Parameter Suggestions** — Recommend RAG adjustments
- **Data Quality Analysis** — Suggest which documents help most

---

## 📡 New API Endpoints

### Learning Dashboard
```
GET /api/learning/adaptive/dashboard
Response: Complete learning dashboard data
```

### User Profile
```
GET /api/learning/adaptive/user-profile/{user_id}
Response: User-specific profile and personalized parameters
```

### Cache Statistics
```
GET /api/learning/adaptive/cache-stats
Response: Query cache performance metrics
```

### Query Improvement Suggestions
```
POST /api/learning/adaptive/suggest-improvements
Body: { "query": "..." }
Response: Rewrite suggestions and similar cached answers
```

### Topic Performance
```
GET /api/learning/adaptive/performance/{topic}
Response: Performance analysis for a specific query topic
```

### Optimization Insights
```
GET /api/learning/adaptive/optimization-insights
Response: System-wide optimization recommendations
```

### All Users Statistics
```
GET /api/learning/adaptive/all-users-stats
Response: Aggregated statistics across all users
```

### Enhanced Feedback Submission
```
POST /api/feedback
Body: {
  "query": "...",
  "answer": "...",
  "rating": 5,
  "sources": [...],
  "user_id": "user_123",
  "topic": "loan_procedures",
  "response_time_ms": 350,
  "comment": "..."
}
Response: Feedback recorded + learning updated
```

---

## 🎓 Learning System Components

### 1. QueryRewriter
**Location**: `backend/adaptive_learning.py`

Learns to improve poorly-performing queries:
```python
from adaptive_learning import adaptive_manager

# Get rewrite suggestions
suggestion = adaptive_manager.query_rewriter.suggest_rewrite(
    query="Tell me about loan",
    low_rating=True
)
# Returns: "Tell me about loan procedures (regulatory reference)"
```

### 2. UserProfileManager
**Location**: `backend/adaptive_learning.py`

Tracks and personalizes by user:
```python
# Update user profile
profile = adaptive_manager.user_profiles.update_user_profile(
    user_id="user_123",
    query="What is KCC?",
    rating=5,
    sources=[...],
    response_time=250
)

# Get personalized parameters
params = adaptive_manager.user_profiles.get_personalized_params("user_123")
# Returns: { "top_k": 6, "temperature": 0.05 }
```

### 3. QueryClusteringEngine
**Location**: `backend/adaptive_learning.py`

Manages query caching and similarity:
```python
# Cache a high-quality answer
adaptive_manager.query_clustering.cache_query(
    query="What is RBI repo rate?",
    answer="Based on latest circular...",
    rating=5,
    sources=[...]
)

# Find similar cached query
cached = adaptive_manager.query_clustering.find_similar_cached(
    query="What is the RBI repo rate?"
)
# Returns: Similar cached answer if similarity >= 85%
```

### 4. PerformanceMetrics
**Location**: `backend/adaptive_learning.py`

Tracks system performance:
```python
# Record interaction
adaptive_manager.performance_metrics.record_interaction(
    query="How to apply for loan?",
    rating=4,
    response_time=450,
    chunks_found=8,
    source_count=3,
    topic="loan_procedures"
)

# Get topic analysis
analysis = adaptive_manager.performance_metrics.get_topic_analysis("loan_procedures")
# Returns: {
#   "topic": "loan_procedures",
#   "avg_rating": 4.2,
#   "avg_response_time_ms": 380,
#   "rating_trend": "improving"
# }
```

---

## 🚀 Using Self-Learning in Your Application

### 1. Send User ID with Chat Request
```javascript
// In frontend/app.js
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "What are the RBI guidelines?",
    session_id: currentSessionId,
    user_id: "staff_001"  // NEW: For user profiling
  }),
});
```

### 2. Submit Detailed Feedback
```javascript
// Include topic and response time for better learning
fetch('/api/feedback', {
  method: 'POST',
  body: JSON.stringify({
    query: "What is KCC?",
    answer: "Kisan Credit Card is...",
    rating: 5,
    sources: [...],
    user_id: "staff_001",        // NEW
    topic: "credit_schemes",      // NEW
    response_time_ms: 250,        // NEW
    comment: "Accurate and helpful"
  }),
});
```

### 3. Access Learning Dashboard
```
Navigate to: http://[server]:8000/learning
Or click "🧠 Learning Dashboard" in sidebar
```

### 4. Monitor Performance
```javascript
// Get all user stats
const response = await fetch('/api/learning/adaptive/all-users-stats');
const stats = await response.json();
console.log(`${stats.stats.total_users} users, avg rating: ${stats.stats.avg_rating_all_users}`);
```

---

## 📈 Performance Improvements Over Time

As the system learns, you'll see:

### Week 1-2: Data Collection Phase
- System records baseline performance
- Feedback accumulates
- No optimizations yet (building knowledge base)

### Week 2-3: Pattern Recognition Phase
- User profiles emerge
- Common queries cached
- Performance trends identified
- Optimization suggestions generated

### Week 3+: Optimization Phase
- RAG parameters automatically tuned
- Response times improve
- Answer quality increases
- New users benefit from learned patterns

**Expected Metrics:**
- ⏱️ Response time: -30% to -50%
- ⭐ Average rating: +0.3 to +1.0 points
- 💾 Cache hit rate: 15-40% for repeat queries
- 🎯 Personalization: +20% relevance improvement

---

## 🔧 Configuration

### Enable/Disable Learning
Edit `backend/config.py`:
```python
# Self-learning system configuration
ENABLE_ADAPTIVE_LEARNING = True
CACHE_SIMILARITY_THRESHOLD = 0.85
USER_PROFILE_RETENTION_DAYS = 90
MAX_CACHE_SIZE = 1000
```

### Adjust Learning Parameters
```python
# Query cache settings
CACHE_MIN_RATING = 4  # Only cache high-quality (4+) answers

# User profile settings
USER_PROFILE_RETENTION = 90  # Days to keep profiles

# Performance tracking
PERFORMANCE_METRICS_RETENTION = 365  # Days of history

# Optimization
OPTIMIZATION_UPDATE_FREQUENCY = 5  # Update every N feedback items
```

---

## 📊 Data Files

Learning data is stored in:
```
backend/learning/
├── feedback.jsonl              # All user feedback records
├── stats.json                  # Aggregate statistics
├── insights.json               # System insights & recommendations
└── adaptive_db/
    ├── query_clusters.json     # Query similarity clusters
    ├── user_profiles.json      # Individual user profiles
    ├── query_cache.json        # Cached Q&A pairs
    ├── performance_metrics.json # Performance by topic
    └── query_rewrites.jsonl    # Query rewrite history
```

### Export Learning Data
```python
# In your backend
from learning import learning_manager

# Export all data
export_data = learning_manager.export_learning_data()
with open('learning_export.json', 'w') as f:
    f.write(export_data)
```

---

## 🔒 Privacy & Data Security

- **Local Storage Only**: All learning data stays on your internal network
- **No Cloud Sync**: No data leaves your server (unless explicitly configured)
- **User Anonymization**: User IDs can be anonymized/pseudonymized
- **Data Retention**: Configure retention policies in config.py
- **GDPR Compliant**: Easy to delete user profiles on request

```python
# Delete user profile (GDPR compliance)
adaptive_manager.user_profiles.profiles.pop("user_123", None)
adaptive_manager.user_profiles.save_profiles()

# Export user data (GDPR right to access)
user_data = adaptive_manager.user_profiles.get_user_profile("user_123")
```

---

## 🎯 Best Practices

### 1. **Encourage Feedback**
- Make feedback buttons visible and easy to click
- Show appreciation for feedback ("Thank you! System learning...")
- Display impact ("Your feedback has helped 23 similar queries")

### 2. **Monitor Learning Health**
- Check dashboard weekly
- Review optimization recommendations
- Watch for performance declines
- Investigate low ratings quickly

### 3. **Validate Learning**
- Test cache hit rates
- Monitor response times
- Check topic coverage
- Verify user satisfaction

### 4. **Maintain Learning Data**
- Backup learning data regularly
- Archive old data periodically
- Monitor database file sizes
- Clean up stale cache entries

### 5. **Continuous Improvement**
- Regular review of dashboard insights
- Implement suggested optimizations
- Update documents based on trends
- Retrain/reindex as needed

---

## 📞 Support & Troubleshooting

### Dashboard Not Loading
1. Check backend is running: `http://localhost:8000/api/status`
2. Verify adaptive_learning.py is imported in main.py
3. Check logs for errors: `backend/logs/main.log`

### Low Cache Hit Rate
- Ensure feedback is being submitted (click rating buttons)
- Check MIN_SIMILARITY_SCORE is not too high
- More diverse queries = lower hit rate (normal)

### User Profiles Not Building
- Verify user_id is being sent with chat requests
- Check `/api/learning/adaptive/all-users-stats` endpoint
- Review user profile file: `backend/learning/adaptive_db/user_profiles.json`

### Performance Declining
- Check admin panel for document quality
- Review low-rated answers for patterns
- Consider adding more relevant documents
- Check if TOP_K_RESULTS needs adjustment

---

## 🚀 Next Steps

1. **Deploy System** — Run the enhanced system and gather baseline metrics
2. **Collect Feedback** — Encourage users to rate answers (Week 1-2)
3. **Monitor Trends** — Check dashboard weekly (Week 2-3)
4. **Implement Suggestions** — Follow optimization recommendations (Week 3+)
5. **Measure Impact** — Compare metrics before/after learning

---

## 📚 Related Documentation

- [README.md](README.md) — System overview
- [QUICKSTART.md](QUICKSTART.md) — Getting started guide
- [DEPLOYMENT.md](DEPLOYMENT.md) — Production deployment
- [admin.html](/admin) — Admin panel for document management
- [learning.html](/learning) — Learning dashboard

---

## 🎓 Example: Complete Learning Workflow

```
1. User asks: "What is KCC?"
   └─ System returns: "Kisan Credit Card is..." (Rating: 4.8)
   
2. User clicks 👍 (feedback)
   └─ Backend records:
      - Query cached (rating > 4)
      - User profile updated
      - Performance metric recorded
      - Learning DB updated

3. User 2 asks similar query: "Tell me about Kisan Credit Card"
   └─ System detects similar cached query (95% similarity)
   └─ Returns cached answer (instant!)
   └─ User satisfied (better experience)

4. Next week, dashboard shows:
   ✓ 2 similar queries served from cache
   ✓ Response time improved 40%
   ✓ User rating for KCC topics: 4.7/5.0
   ✓ Top topic: "Kisan Credit Card" (15 queries)
   ✓ Recommendation: "Add more KCC examples"

5. Admin uploads more KCC documents
   └─ System re-indexes
   └─ Next week metrics even better
   └─ Continuous improvement cycle continues
```

---

**🌟 Your system is now self-learning and continuously improving!**
