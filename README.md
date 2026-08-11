# 🔍 TruthLens — AI Fake News Detection System

> Advanced NLP-powered misinformation detector with sentiment analysis, bias detection, clickbait scoring, readability metrics, and persistent history.

---

## 📁 Project Structure

```
fake-news-detector/
├── backend/
│   ├── main.py              ← FastAPI + spaCy NLP backend
│   ├── requirements.txt     ← Python dependencies
│   ├── Dockerfile           ← Docker image definition
│   ├── Procfile             ← For Heroku / Railway / Render
│   └── runtime.txt          ← Python version pin
├── frontend/
│   ├── index.html           ← Main UI
│   ├── style.css            ← Glassmorphism dark theme
│   ├── app.js               ← All interactivity & API calls
│   └── config.js            ← ⚙️ API URL switcher (edit this!)
├── docker-compose.yml       ← Run everything with one command
├── nginx.conf               ← Nginx config for Docker frontend
├── render.yaml              ← One-click Render.com deploy
├── netlify.toml             ← Netlify frontend deploy config
├── start.bat                ← 🪟 Windows one-click launcher
├── start.sh                 ← 🐧 Linux/Mac one-click launcher
└── .gitignore
```

---

## 🚀 Option 1: Run Locally (Quickest)

### Windows — Double-click `start.bat`
The file starts both servers and opens your browser automatically.

### Manual (any OS)
```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
python -m http.server 5000
```

Open → **http://localhost:5000**

---

## 🐳 Option 2: Docker (Recommended for Production)

> Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# Build and start both services
docker-compose up --build

# Run in background
docker-compose up --build -d

# Stop all services
docker-compose down
```

Open → **http://localhost:5000**

---

## ☁️ Option 3: Deploy to Render.com (Free Backend Hosting)

1. Push this project to a **GitHub repository**
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Deploy**
5. Copy your backend URL: `https://your-app.onrender.com`
6. Edit `frontend/config.js`:
   ```js
   const CONFIG = {
       API_BASE: 'https://your-app.onrender.com'
   };
   ```

---

## 🌐 Option 4: Deploy Frontend to Netlify (Free Static Hosting)

1. Push to GitHub
2. Go to [netlify.com](https://netlify.com) → **Add new site → Import from Git**
3. Select your repo
4. Set **Publish directory** to `frontend`
5. In `netlify.toml`, replace `YOUR-BACKEND-URL` with your Render URL
6. Click **Deploy Site**

---

## 🚂 Option 5: Deploy to Railway (Easiest Cloud Deploy)

1. Go to [railway.app](https://railway.app) → **New Project**
2. Select **Deploy from GitHub repo**
3. Set the **Root Directory** to `backend`
4. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
6. Copy your Railway URL and paste it in `frontend/config.js`

---

## ⚙️ Changing the API URL (For Deployment)

Edit **`frontend/config.js`** — this is the only file you need to change:

```js
// LOCAL DEVELOPMENT
const CONFIG = { API_BASE: 'http://127.0.0.1:8000' };

// PRODUCTION (after deploying backend)
const CONFIG = { API_BASE: 'https://your-backend.onrender.com' };
```

---

## 🔬 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/`      | Health check |
| `POST` | `/analyze` | Analyze text — returns full NLP results |
| `GET`  | `/history` | Last 20 analyses from DB |
| `DELETE` | `/history` | Clear all history |
| `GET`  | `/stats`   | Breakdown of total analyses |

**Interactive API docs**: `http://127.0.0.1:8000/docs`

---

## 🧠 Features

| Feature | Technology |
|---|---|
| Named Entity Recognition | spaCy `en_core_web_sm` |
| Sentiment Analysis | Custom lexicon-based model |
| Bias Detection | Political keyword scoring |
| Clickbait Detection | Regex pattern matching |
| Readability Score | Flesch Reading Ease formula |
| Writing Style | Passive voice, quote, URL detection |
| Virality Risk | Composite risk index |
| History Storage | SQLite (auto-created) |
| REST API | FastAPI + Uvicorn |

---

## 📋 Requirements

- Python 3.9+
- pip
- Modern web browser (Chrome, Firefox, Edge)
- Docker (optional, for Docker deployment)
