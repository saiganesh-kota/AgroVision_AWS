# AgroVision AI v3 — Intelligent Crop Disease Detection Platform

## AWS "Ship It" deployment

This repo deploys with a live URL: **Amazon ECS Express Mode** (backend, containerized on Fargate),
**Vercel** (frontend), **S3** (scan history, uploads, model weights).
See **[DEPLOY.md](./DEPLOY.md)** for the full walkthrough and
`infra/cloudformation.yaml` for the one-command foundation stack.

## What's New in v3

### 🔐 Authentication
- Real Sign In / Sign Up pages (no more "demo mode")
- User accounts stored locally with name, email, phone, state
- Logged-in user shown in sidebar with state info
- Floating ChatBot widget removed (use the dedicated RaithuMitra page instead)

### 🌾 Crop Type — Fully Linked
- Frontend crop selector now sends `crop_type` to backend
- `pipeline.py` accepts and uses it: if farmer selects "Tomato", result says "Tomato" not just "Healthy/Diseased"
- `disease_status` field added to result for the raw model output

### 🍃 Leaf Validator — Strict (Face Detection Added)
- OpenCV Haar Cascade face detection: **human faces are hard-rejected**
- Improved brown/yellow ratio detection for diseased leaves
- Tighter thresholds — food, objects, sky all rejected properly

### 🤖 AI / Keys
- **Anthropic API key completely removed** — Gemini only
- Chat uses `gemini-2.5-flash → 2.0-flash → 1.5-flash` fallback chain

### 🏛️ Government Schemes — Fixed & Expanded
- Route registration bug fixed (was defined after startup block)
- 5 new schemes added: PMKSY, PKVY, RKVY, NMOOP, MIDH
- New `/schemes/for-crop` endpoint — auto-matched to detected crop
- AnalysisPage now shows applicable schemes after every scan

### 📅 Crop Calendar (New Feature)
- Phase-wise farming guide for 5 crops (Wheat, Rice, Tomato, Cotton, Maize)
- Monthly task lists with risk levels
- Auto-selects crop from last scan result

### 📈 Yield & Profit Estimator (New Feature)
- AI-powered yield forecast using pH, rainfall, fertilizer, irrigation, disease severity
- MSP-based revenue, cost, profit and ROI calculation
- Supports 8 crops with realistic cost models
- Factor analysis breakdown (what's limiting your yield)

### 🔄 Dashboard
- Refresh button for real-time data update
- Feature quick-access cards (Calendar, Yield Estimator, Schemes)
- Greets user by name from their account

---

## Setup

### Backend
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Edit .env — add your GEMINI_API_KEY
python app.py
```

### Frontend
```bash
cd frontend
npm install
# Edit .env — set VITE_API_URL=http://localhost:5001
npm run dev
```

### Environment Variables

**backend/.env**
```
PORT=5000
GEMINI_API_KEY=your_key_here          # Required for chat
OPENWEATHER_API_KEY=your_key_here     # Optional (mock data if empty)
GOOGLE_PLACES_API_KEY=your_key_here   # Optional (empty = no suppliers)
```

**frontend/.env**
```
VITE_API_URL=http://localhost:5001
```

---

## Architecture

```
frontend/ (React + Vite + TailwindCSS)
├── pages/
│   ├── AuthPage.jsx          ← Sign In / Sign Up (NEW)
│   ├── DashboardPage.jsx     ← Overview + quick features
│   ├── ScanPage.jsx          ← Upload leaf → ML pipeline
│   ├── AnalysisPage.jsx      ← Detailed results + matched schemes
│   ├── CropCalendarPage.jsx  ← NEW: seasonal farming guide
│   ├── YieldEstimatorPage.jsx← NEW: profit forecast
│   ├── SchemesPage.jsx       ← Govt schemes browser
│   ├── GeoMapPage.jsx        ← Disease spread map
│   ├── HistoryPage.jsx       ← Past scans
│   └── ChatPage.jsx          ← RaithuMitra AI assistant
backend/ (Flask + Python)
├── app.py                    ← API routes (Gemini only, schemes fixed)
├── pipeline.py               ← Full ML pipeline (crop_type linked)
├── leaf_validator.py         ← Face detection + leaf gating (IMPROVED)
├── schemes_data.py           ← 13 govt schemes + contacts
└── models/                   ← Pre-trained .keras + .pkl models
```

## Patent Features
1. Multi-modal leaf disease detection (image + environment)
2. Reinforcement Learning recommendation engine
3. Geo-intelligence outbreak prediction
4. 7-day disease progression forecasting
5. Adaptive weight feedback loop (auto-retraining)
6. Treatment comparison with value scoring
7. Explainability (XAI) factors
8. Automated decision pipeline
9. Crop-matched government scheme surfacing (NEW)
10. Crop calendar with disease risk overlay (NEW)
