# 🚀 BankAssist AI - Quick Start Guide (Updated)

> **Enterprise Bank Circular Intelligence - Now with Web Scraping, Security & Analytics**

---

## ✨ What's New in This Version

### 🌐 **Web Scraping is Now WORKING!**
- Fetches latest circulars from **RBI, NABARD, SEBI** automatically
- Keep your knowledge base updated with regulatory changes
- Admin Panel → "Secondary Learning" → Click "Start Web Fetch Now"

### 🔒 **Enhanced Security**
- Rate limiting to prevent abuse (100 requests/minute)
- IP whitelisting support
- File-based logging for audits

### 📊 **Better Analytics**
- Query logging for insights
- Activity logs in admin panel
- Performance metrics

### ⚙️ **Admin Panel Improvements**
- Web scraping controls
- Document management
- Real-time status monitoring
- Query history

---

## 📥 Installation (5 minutes)

### **Step 1: Run Setup**
Double-click **`setup.bat`** — this will:
- ✅ Verify Python & Ollama
- ✅ Install dependencies
- ✅ Download LLM models (~2GB)

### **Step 2: Launch Server**
Double-click **`start.bat`** — opens the server

### **Step 3: Access the App**
- **Chat:** http://localhost:8000
- **Admin:** http://localhost:8000/admin

---

## 💬 Using the Chat

1. **Type a question:**
   - "What are the latest RBI KYC guidelines?"
   - "Show me NABARD loan refinance limits"
   - "What are SEBI regulations for digital securities?"

2. **Get grounded answers** from your uploaded circulars
3. **Click sources** to see which circular was cited

---

## ⚙️ Admin Panel - What You Can Do

### **Upload Circulars**
- PDF, DOCX, XLSX, TXT files
- Drag & drop or click to browse
- Auto-indexed into knowledge base

### **Fetch Web Circulars** (NEW!)
- Admin Panel → "Secondary Learning"
- Click "🌐 Start Web Fetch Now"
- System fetches RBI, NABARD, SEBI public circulars
- Status updates in real-time

### **Monitor System**
- View stats: internal docs, chunks, queries
- See activity log
- Check document list with authorities
- Delete outdated circulars

---

## 🌐 Web Scraping (NEW!)

### How It Works
1. Click "Start Web Fetch Now" in admin panel
2. System connects to RBI, NABARD, SEBI websites
3. Downloads latest public circulars
4. Indexes them into knowledge base
5. Status updates show progress

### What Gets Scraped
- **RBI** - Notifications & Master Circulars
- **NABARD** - Lending Guidelines & Circulars  
- **SEBI** - Regulations & Notifications

### Benefits
- ✅ Automatic knowledge base updates
- ✅ Regulatory compliance
- ✅ No manual document collection
- ✅ Real-time information

---

## 🔐 Security Features

### Rate Limiting
- **100 requests per 60 seconds** (default)
- Prevents API abuse
- Can be adjusted in `backend/config.py`

### IP Whitelisting (Optional)
Edit `backend/config.py`:
```python
ADMIN_IP_WHITELIST = ["192.168.1.*", "127.0.0.1"]
```

### Logging
- All queries logged to `logs/queries.log`
- Server logs in `logs/main.log`
- Useful for audits and troubleshooting

---

## 📊 Configuration

Edit `backend/config.py` to customize:

### LLM Model (Speed vs Quality)
```python
LLM_MODEL = "llama3.2"        # ⚡ Fast, good quality (default)
# LLM_MODEL = "mistral"        # ⚡⚡ Faster
# LLM_MODEL = "llama3.1:8b"    # ⚡⚡ Fast, better quality
# LLM_MODEL = "gemma2:9b"      # ⭐ Best quality, slowest
```

### RAG Tuning
```python
TOP_K_RESULTS = 8              # More results = better recall
MIN_SIMILARITY_SCORE = 0.10    # Lower = more relaxed matching
CHUNK_SIZE = 1000              # Larger = more context per chunk
```

### Performance
```python
ENABLE_QUERY_CACHING = True    # Cache recent queries
CACHE_TTL_SECONDS = 300        # 5 minutes
MAX_WORKERS = 4                # Parallel tasks
```

---

## 📁 Project Structure

```
bank-llm/
├── backend/
│   ├── main.py                 # FastAPI server (NEW: logging, rate limit)
│   ├── config.py               # Settings (NEW: scraping URLs, security)
│   ├── rag_engine.py          # RAG pipeline
│   ├── document_processor.py  # PDF/DOCX parsing
│   ├── web_scraper.py         # Web scraping (FIXED!)
│   └── requirements.txt        # Python packages
├── frontend/
│   ├── index.html             # Chat UI
│   ├── admin.html             # Admin panel (NEW: web scraping UI)
│   ├── app.js                 # Chat logic
│   └── style.css              # Styling
├── circulars/                 # Drop PDFs here
├── vector_db/                 # Auto-created (knowledge base)
├── logs/                      # Auto-created (activity logs)
├── setup.bat                  # Installation (IMPROVED!)
├── start.bat                  # Launcher
├── DEPLOYMENT.md              # Production guide (NEW!)
├── IMPROVEMENTS.md            # What changed (NEW!)
└── README.md                  # Original docs
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Ollama not found"** | Install from https://ollama.ai/download |
| **"Port 8000 in use"** | Change `SERVER_PORT` in `backend/config.py` |
| **"Can't access from LAN"** | Check Windows Firewall → Allow port 8000 |
| **Slow responses** | Use faster model: `LLM_MODEL = "llama3.2"` |
| **Web scraping fails** | Check internet connection; see `logs/scraping.log` |
| **No answers found** | Upload more circulars first |

For more help, see **`DEPLOYMENT.md`** troubleshooting section.

---

## 📖 Documentation

- **`README.md`** - Original features & overview
- **`DEPLOYMENT.md`** - Production guide (NEW!)
- **`IMPROVEMENTS.md`** - What was fixed (NEW!)
- **`OCR_SETUP.md`** - Scanned PDF support
- **`setup.bat`** - Installation script
- **`start.bat`** - Server launcher

---

## 🎯 Key Features

✅ **RAG Architecture** - Grounded answers from documents  
✅ **100% Private** - No cloud, no data sharing  
✅ **Multi-Format** - PDF, DOCX, XLSX, TXT  
✅ **Automatic Citations** - Every answer shows source  
✅ **Web Scraping** - RBI/NABARD/SEBI integration (NEW!)  
✅ **Rate Limiting** - Security & abuse prevention (NEW!)  
✅ **Query Logging** - Analytics & audits (NEW!)  
✅ **Admin Panel** - Full document management  
✅ **Conversation History** - Track all chats  
✅ **Enterprise Ready** - Production deployment guide (NEW!)  

---

## 🚀 Getting Started

1. **Setup:** Double-click `setup.bat`
2. **Launch:** Double-click `start.bat`
3. **Access:** Open http://localhost:8000
4. **Upload:** Go to admin panel, upload circulars
5. **Chat:** Start asking questions!

For enterprise deployment, see **`DEPLOYMENT.md`**.

---

## 💡 Example Questions to Ask

- "What is the current RBI repo rate?"
- "Explain NABARD's priority sector lending guidelines"
- "What are SEBI's KYC requirements for digital securities?"
- "Show me the latest circular on digital banking security"
- "What are the NPA classification norms as per latest RBI circular?"

---

**Status: ✅ Production Ready - Ready for Enterprise Use**

*For detailed deployment, security, and troubleshooting info, see `DEPLOYMENT.md`*
