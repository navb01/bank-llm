# 🚀 BankAssist AI - Deployment & Production Guide

> **Enterprise-Grade Bank Circular Intelligence System**

---

## ✅ Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] Windows 10/11 with 8GB+ RAM
- [ ] Python 3.11+ installed and in PATH
- [ ] Ollama installed from https://ollama.ai/download
- [ ] Internet connection for initial setup
- [ ] Admin access to the deployment machine
- [ ] Tesseract-OCR installed (optional, for scanned PDFs)

---

## 🔧 Step 1: Initial Setup

### First-Time Installation

1. **Double-click `setup.bat`** from the project root
   - This will:
     - Verify Python and Ollama installation
     - Install all Python dependencies
     - Download LLM model (llama3.2, ~2GB)
     - Download embedding model (nomic-embed-text)
   - Setup takes 15-30 minutes depending on internet speed

2. **Setup completes when you see:**
   ```
   ✓ Setup Complete!
   ```

---

## 🟢 Step 2: Starting the Server

### Launch the Application

Double-click **`start.bat`** from the project root.

You'll see:
```
============================================================
    Server Status
============================================================

    🌐 Chat Interface:   http://localhost:8000
    ⚙️  Admin Panel:      http://localhost:8000/admin
    🔗 LAN Access:       http://192.168.1.100:8000
```

### For Bank Staff

Share the **LAN Access URL** with employees on the same network.

---

## 📊 Step 3: Adding Circulars to the Knowledge Base

### Option A: Using Admin Panel (Recommended)

1. Open Admin Panel: `http://SERVER_IP:8000/admin`
2. Click **"Upload Circulars"**
3. Drag & drop PDF, DOCX, XLSX files
4. Click **"Upload Selected Files"**

### Option B: Drop Files in Folder

1. Copy circulars to `./circulars/` folder
2. Go to Admin Panel → **"Re-ingest All from Folder"**

### Option C: Auto-Index Web Circulars

1. Admin Panel → **"Secondary Learning (Web)"**
2. Click **"Start Web Fetch Now"**
3. System fetches latest RBI, NABARD, SEBI public circulars

---

## 🌐 Step 4: Using the Chat Interface

1. Open browser: `http://localhost:8000`
2. Type your question: _"What are the latest RBI guidelines on KYC?"_
3. System returns answers with **citations** from uploaded circulars

### Features

- ✅ **Grounded Answers** - Only from uploaded documents
- ✅ **Auto-Citations** - Every answer shows source circular
- ✅ **Multi-Format** - Supports PDF, DOCX, XLSX, TXT
- ✅ **Conversation History** - All chats saved locally
- ✅ **100% Private** - No cloud, no data sharing

---

## ⚙️ Configuration

Edit `backend/config.py` to customize:

### LLM Model
```python
LLM_MODEL = "llama3.2"  # Options: mistral, llama3.1:8b, gemma2:9b
```

### Server Port
```python
SERVER_PORT = 8000  # Change if port is already in use
```

### Rate Limiting (Production)
```python
ENABLE_RATE_LIMITING = True
RATE_LIMIT_REQUESTS = 100     # per 60 seconds
```

### Logging
```python
ENABLE_QUERY_LOGGING = True
QUERY_LOG_FILE = "logs/queries.log"
```

### Vector DB Tuning
```python
TOP_K_RESULTS = 8           # Chunks to retrieve per query
MIN_SIMILARITY_SCORE = 0.10 # Relevance threshold
CHUNK_SIZE = 1000           # Characters per chunk
```

---

## 🔒 Security for Production

### 1. IP Whitelisting (Admin Panel)

Edit `backend/config.py`:
```python
ADMIN_IP_WHITELIST = ["192.168.1.*", "127.0.0.1"]
```

### 2. Windows Firewall Configuration

Allow only specific IPs:
```powershell
# Run as Administrator
netsh advfirewall firewall add rule name="BankAssist" ^
  dir=in action=allow protocol=tcp localport=8000 ^
  remoteip=192.168.1.0/24
```

### 3. HTTPS in Production

For external access, use a reverse proxy with SSL:
- **Nginx** - Recommended for Linux/Docker
- **IIS** - Built-in Windows reverse proxy
- **Apache** - Universal alternative

### 4. Authentication (Optional)

Add HTTP Basic Auth to `main.py`:
```python
from fastapi_security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.post("/api/chat")
async def chat(request: ChatRequest, credentials: HTTPBasicCredentials = Depends(security)):
    # Verify credentials...
    return response
```

---

## 📈 Performance Tuning

### For Small Banks (< 100 users)
```python
CHUNK_SIZE = 800
TOP_K_RESULTS = 5
LLM_MODEL = "llama3.2"          # Fast, good quality
```

### For Large Banks (> 500 users)
```python
CHUNK_SIZE = 1200
TOP_K_RESULTS = 10
LLM_MODEL = "gemma2:9b"         # Better quality, slower
# Use database-backed sessions instead of in-memory
```

### Memory Optimization
```python
# In backend/config.py
MAX_WORKERS = 2              # Fewer parallel tasks
CACHE_TTL_SECONDS = 600      # Longer cache
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Ollama not found"** | Reinstall Ollama. Ensure it's in PATH: `ollama --version` |
| **"Python not found"** | Install Python 3.11+. Check "Add to PATH" during setup |
| **Slow responses** | Use faster model: `llama3.2`. Check RAM usage |
| **"Port 8000 already in use"** | Change `SERVER_PORT` in config.py |
| **Can't connect from LAN** | Check Windows Firewall. Allow port 8000 |
| **Out of memory errors** | Reduce `CHUNK_SIZE` in config.py. Restart server |
| **Poor answer quality** | Upload more/better quality circulars. Adjust `MIN_SIMILARITY_SCORE` |

---

## 📊 Monitoring & Logs

### Check Server Status
- Admin Panel: `http://SERVER_IP:8000/admin` → Status indicator

### View Logs
- **Server logs:** `./logs/main.log`
- **Query logs:** `./logs/queries.log`
- **Scraping logs:** `./logs/scraping.log`

### Monitor System
Use Windows Task Manager to check:
- Python process CPU/RAM usage
- Ollama process status
- Network connections

---

## 🔄 Maintenance

### Daily
- Monitor admin panel for errors
- Check that circulars are being indexed

### Weekly
- Review query logs for improvements
- Check disk space (vector_db grows over time)

### Monthly
- Update LLM models: `ollama pull llama3.2`
- Back up vector_db folder
- Review and organize circulars

### Quarterly
- Clear old conversation history (optional)
- Optimize chunk size based on usage patterns
- Consider adding more circulars

---

## 📤 Backup & Disaster Recovery

### Backup Vector DB
```powershell
# Run as Administrator
robocopy "vector_db" "D:\Backup\bankllm_vector_db" /MIR
```

### Backup Circulars Folder
```powershell
robocopy "circulars" "D:\Backup\bankllm_circulars" /MIR
```

### Restore from Backup
```powershell
robocopy "D:\Backup\bankllm_vector_db" "vector_db" /MIR
```

---

## 🚢 Docker Deployment (Advanced)

For enterprise deployment across multiple servers:

1. **Create Dockerfile** (provided separately)
2. **Build image:** `docker build -t bankllm:latest .`
3. **Run container:** `docker run -p 8000:8000 bankllm:latest`

---

## 📞 Support & Issues

1. Check logs: `logs/main.log`
2. Verify Ollama: `ollama list`
3. Test connectivity: `curl http://localhost:8000/api/status`
4. Reinstall if needed: Run `setup.bat` again

---

## 📋 System Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 20 GB free | 50 GB free |
| **CPU** | Intel i5 | Intel i7 / Ryzen 7 |
| **Network** | 1 Mbps (after setup) | 10+ Mbps |

---

## ✨ Version Info

- **Version:** 1.0
- **Status:** Production Ready
- **Last Updated:** 2026-05-25
- **Support:** Enterprise deployments available

---

**Ready to deploy? Start with `setup.bat` → `start.bat` → Visit `http://localhost:8000`** 🚀
