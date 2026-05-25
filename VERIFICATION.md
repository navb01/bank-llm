# ✅ Verification Guide - BankAssist AI

**How to verify everything is working correctly**

---

## 🚀 Step 1: Run Setup

**Command:** Double-click `setup.bat`

**Expected Output:**
```
[OK] Python found
[OK] Ollama found
[STEP 1/4] Upgrading pip...
[STEP 2/4] Installing Python packages...
[OK] Packages installed
[STEP 3/4] Pulling LLM model: llama3.2...
[STEP 4/4] Pulling embedding model: nomic-embed-text
[OK] Setup Complete!
```

**If you see errors:**
- Python not found → Install Python 3.11+ from python.org
- Ollama not found → Install from ollama.ai/download
- Package install fails → Run: `cd backend` then `pip install -r requirements.txt`

---

## 🔧 Step 2: Launch Server

**Command:** Double-click `start.bat`

**Expected Output:**
```
[STEP 1/3] Ensuring dependencies...
[STEP 2/3] Checking Ollama models...
[OK] Ollama connectivity verified
[STEP 3/3] Launching BankAssist Server...

============================================================
    Server Status
============================================================

    🌐 Chat Interface:   http://localhost:8000
    ⚙️  Admin Panel:      http://localhost:8000/admin
    🔗 LAN Access:       http://192.168.x.x:8000

    Press Ctrl+C to stop the server
```

**If you see errors:**
- Port already in use → Edit `backend/config.py`, change `SERVER_PORT`
- Ollama not found → Make sure `ollama serve` is running in another terminal

---

## 🌐 Step 3: Test Chat Interface

### Open Browser
- **Local:** http://localhost:8000
- **LAN:** http://192.168.1.X:8000 (replace X with your IP)

### Expected:
- ✅ Chat interface loads
- ✅ "BankAssist AI" logo visible
- ✅ Suggestion chips displayed
- ✅ Server status shows "Online"

### Test Query
Type: `"Hello, what can you help me with?"`

**Expected Response:**
- Bot says: "I don't have information about this topic in the available circulars and documents..."
- This is CORRECT - you haven't uploaded documents yet!

---

## ⚙️ Step 4: Test Admin Panel

### Open Browser
http://localhost:8000/admin

### Expected:
- ✅ Admin panel loads
- ✅ Status shows "Online"
- ✅ Stats display (all should show 0 initially)
- ✅ "Upload Circulars" card visible
- ✅ "Secondary Learning (Web)" card visible (NEW!)

### Verify Cards Present:
- [x] Upload Circulars
- [x] Secondary Learning (Web) - NEW!
- [x] Activity Log
- [x] Recent Queries
- [x] Knowledge Base Documents

---

## 📤 Step 5: Test Web Scraping (NEW!)

### In Admin Panel:
1. Scroll to "Secondary Learning (Web)" card
2. Click **"🌐 Start Web Fetch Now"** button

### Expected:
- ✅ Progress indicator appears
- ✅ "Scraping in progress..." message
- ✅ Progress bar animates
- ✅ After ~30-60 seconds, completes
- ✅ Shows: "✓ Web scraping: X sources ✓, Y failed"

### If scraping fails:
- Check internet connection
- Check `logs/scraping.log` for details
- Verify firewall allows outbound HTTPS
- Try again - websites may be temporarily unavailable

---

## 📤 Step 6: Test Document Upload

### In Admin Panel:
1. Create a test document (PDF, DOCX, or TXT)
2. Write some sample text with "RBI", "circular", "interest rate"
3. Drag & drop into upload zone
4. Click "Upload Selected Files"

### Expected:
- ✅ Progress bar appears
- ✅ File uploads (should be quick)
- ✅ Toast shows: "✓ filename — X chunks indexed"
- ✅ Activity log shows success
- ✅ Documents table updates with new document

---

## 🔍 Step 7: Test Chat with Documents

### Back in Chat Interface:
1. Type: `"What is mentioned in the uploaded document?"`

### Expected:
- ✅ Bot responds with content from document
- ✅ Shows "📎 1 Sources Referenced"
- ✅ Click to expand and see:
   - Document filename
   - Circular Reference (if recognized)
   - Relevance score

---

## 📊 Step 8: Verify Logging

### Check Logs Folder
Navigate to: `./logs/`

### Should contain:
- [x] `main.log` - Server activity
- [x] `queries.log` - All user queries
- [x] `scraping.log` - Web scraping events

### Expected Content:
**main.log:**
```
2026-05-25 10:30:45 - __main__ - INFO - [OK] Python found
2026-05-25 10:31:00 - __main__ - INFO - Chat query from 127.0.0.1: Hello what can you help...
```

**queries.log:**
```
2026-05-25 10:31:00 - queries - INFO - Q: What is mentioned in the document | Sources: 1 | IP: 127.0.0.1
```

**scraping.log:**
```
2026-05-25 10:35:00 - web_scraper - INFO - Fetching: https://www.rbi.org.in/...
```

---

## 🔐 Step 9: Verify Rate Limiting

### Test Rate Limiting (optional)
Rapidly send multiple requests:
1. Open browser console (F12)
2. Run this JavaScript:
```javascript
for (let i = 0; i < 150; i++) {
  fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'test' + i })
  });
}
```

### Expected:
- First 100 requests succeed
- Request 101+ returns 429 (Too Many Requests)
- After 60 seconds, can send again

---

## ✅ Final Verification Checklist

**Server & Setup:**
- [ ] `setup.bat` runs without errors
- [ ] `start.bat` launches successfully
- [ ] Server shows "Online" status

**Chat Interface:**
- [ ] Loads at http://localhost:8000
- [ ] Shows suggestion chips
- [ ] Can type queries

**Admin Panel:**
- [ ] Loads at http://localhost:8000/admin
- [ ] Shows all stats
- [ ] All cards visible
- [ ] **"Secondary Learning" card present** (NEW!)

**Upload:**
- [ ] Can upload test document
- [ ] Document appears in table
- [ ] Chat can reference document

**Web Scraping (NEW!):**
- [ ] "Start Web Fetch Now" button works
- [ ] Progress indicator shows
- [ ] Completes without errors
- [ ] Results appear in logs

**Logging:**
- [ ] `logs/main.log` created
- [ ] `logs/queries.log` created
- [ ] `logs/scraping.log` created
- [ ] Entries are written

**Rate Limiting:**
- [ ] Works (returns 429 when exceeded)
- [ ] Can be configured in `config.py`

---

## 🎯 What Each Part Does

### Chat Interface (`http://localhost:8000`)
- Users ask questions about circulars
- Bot returns answers with citations
- Conversation history saved locally

### Admin Panel (`http://localhost:8000/admin`)
- Upload new circulars
- **Fetch web circulars (NEW!)**
- Delete old documents
- Monitor system stats
- View activity log

### Backend Server
- **Web scraping** from RBI/NABARD/SEBI (FIXED!)
- **Rate limiting** (NEW!)
- **Query logging** (NEW!)
- RAG pipeline (unchanged)
- Vector database (unchanged)

### Logs
- **main.log** - Server events
- **queries.log** - User queries (NEW!)
- **scraping.log** - Web scraping (NEW!)

---

## 🐛 If Something Doesn't Work

### 1. Check Logs
```powershell
Get-Content .\logs\main.log -Tail 20
```

### 2. Restart Server
- Close `start.bat` (Ctrl+C)
- Run `start.bat` again

### 3. Verify Ollama
```powershell
ollama list
ollama pull llama3.2
```

### 4. Clear & Reinstall
```powershell
cd backend
pip install -r requirements.txt --force-reinstall
```

### 5. Check Firewall
- Windows Defender Firewall
- Inbound rules for port 8000
- Allow python.exe

---

## ✨ Success Indicators

You'll know everything is working when:

1. ✅ `setup.bat` completes successfully
2. ✅ `start.bat` shows "Online" status
3. ✅ Chat loads and shows suggestion chips
4. ✅ Admin panel shows online with stats
5. ✅ Can upload documents
6. ✅ **Can fetch web circulars (NEW!)**
7. ✅ Chat returns answers from documents
8. ✅ Logs are being written
9. ✅ Rate limiting is active
10. ✅ Can access from LAN

---

## 🎉 You're Ready!

If all checks pass, your BankAssist AI system is:
- ✅ Fully installed
- ✅ Properly configured
- ✅ Actively logging
- ✅ Protecting against abuse
- ✅ Ready for production use!

---

**Next Steps:**
1. Upload your bank circulars
2. Test with real queries
3. Configure settings as needed
4. Review `DEPLOYMENT.md` for production use
5. Set up backups and monitoring

**Questions? Check:**
- `QUICKSTART.md` - Usage guide
- `DEPLOYMENT.md` - Production guide
- `IMPROVEMENTS.md` - What changed
- `logs/main.log` - Error details

---

**Status: ✅ Ready to Deploy**
