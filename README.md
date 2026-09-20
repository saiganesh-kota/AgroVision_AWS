# 🌾 AgroVision AI v3 — Intelligent Crop Disease Detection Platform

> AI-powered crop diagnosis, treatment recommendations, and farm intelligence — deployed live on AWS + Vercel.

[![Backend](https://img.shields.io/badge/backend-Flask%20%2B%20Python-3776AB)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)]()
[![Deploy](https://img.shields.io/badge/deploy-ECS%20Fargate%20%2B%20Vercel-orange)]()
[![License](https://img.shields.io/badge/status-hackathon%20build-brightgreen)]()

---

## 📐 Architecture

```mermaid
flowchart LR
    subgraph Client["👨‍🌾 Farmer's Device"]
        UI[React + Vite Frontend]
    end

    subgraph Vercel["▲ Vercel"]
        UI
    end

    subgraph AWS["☁️ AWS"]
        subgraph ECS["Amazon ECS · Fargate"]
            API[Flask Backend<br/>app.py]
            Pipeline[ML Pipeline<br/>pipeline.py]
            Agents[Disease · Soil · Weather ·<br/>Treatment · Commerce logic]
        end
        S3[(S3 Bucket<br/>uploads · scan history · model weights)]
        ECR[(ECR<br/>Docker image registry)]
    end

    Gemini[[Gemini API<br/>RaithuMitra Chat]]

    UI -- "HTTPS / REST" --> API
    API --> Pipeline --> Agents
    API <--> S3
    Agents -. explanations .-> Gemini
    ECR -. "docker push / pull" .-> ECS

    style Client fill:#eef6ff,stroke:#3b82f6
    style Vercel fill:#000,color:#fff,stroke:#333
    style AWS fill:#fff7e6,stroke:#f59e0b
    style ECS fill:#e8f5e9,stroke:#43a047
```

---

## 🔬 Scan → Diagnosis → Recommendation flow

```mermaid
sequenceDiagram
    actor Farmer
    participant UI as Frontend
    participant API as Backend (app.py)
    participant ML as ML Pipeline
    participant S3 as S3 Storage
    participant Gemini as Gemini (RaithuMitra)

    Farmer->>UI: Upload leaf photo + select crop
    UI->>API: POST /predict (image, crop_type, weather, location)
    API->>S3: Store uploaded image
    API->>ML: Run leaf validation + disease classification
    ML-->>API: disease_name, confidence, severity, crop
    API->>API: Match govt schemes for detected crop
    API->>Gemini: Request plain-language explanation
    Gemini-->>API: Natural-language summary
    API->>S3: Persist scan + result to history
    API-->>UI: Diagnosis + treatment + schemes + chat-ready summary
    UI-->>Farmer: Results, confidence, recommended action
```

---

## ✨ What's New in v3

| Area | Highlights |
|---|---|
| 🔐 **Authentication** | Real Sign In / Sign Up (no more demo mode); accounts stored with name, email, phone, state; logged-in user shown in sidebar |
| 🌾 **Crop Type** | Frontend crop selector now flows through to `pipeline.py` — results say "Tomato: Leaf Blight", not just "Diseased" |
| 🍃 **Leaf Validator** | OpenCV Haar Cascade face detection hard-rejects human faces; tighter brown/yellow thresholds reject food/objects/sky |
| 🤖 **AI / Chat** | Anthropic key removed — Gemini only, with `2.5-flash → 2.0-flash → 1.5-flash` fallback chain |
| 🏛️ **Govt Schemes** | Route bug fixed; 5 new schemes (PMKSY, PKVY, RKVY, NMOOP, MIDH); new `/schemes/for-crop` auto-match endpoint |
| 📅 **Crop Calendar** *(new)* | Phase-wise guide for 5 crops with monthly tasks + risk levels, auto-selected from last scan |
| 📈 **Yield & Profit Estimator** *(new)* | MSP-based revenue/cost/ROI forecast from pH, rainfall, fertilizer, irrigation, severity — 8 crops |
| 🔄 **Dashboard** | Live refresh, quick-access feature cards, personalized greeting |

---

## 🚀 Quick Start (Local Development)

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# edit .env — add your GEMINI_API_KEY
python app.py
```

### Frontend

```bash
cd frontend
npm install
# edit .env — set VITE_API_URL=http://localhost:5001
npm run dev
```

---

## ⚙️ Environment Variables

**`backend/.env`**

| Variable | Required | Notes |
|---|---|---|
| `PORT` | — | defaults to `5000` |
| `GEMINI_API_KEY` | ✅ | powers RaithuMitra chat |
| `OPENWEATHER_API_KEY` | optional | falls back to mock data if empty |
| `GOOGLE_PLACES_API_KEY` | optional | empty = no supplier suggestions |

**`frontend/.env`**

| Variable | Required |
|---|---|
| `VITE_API_URL` | ✅ — e.g. `http://localhost:5001` |

---

## 🗂️ Project Structure

```mermaid
flowchart TB
    root["📁 agroaws/"]
    root --> fe["📁 frontend/"]
    root --> be["📁 backend/"]
    root --> infra["📁 infra/"]
    root --> deploy["📄 DEPLOY.md"]

    fe --> fe1["pages/AuthPage.jsx — sign in/up"]
    fe --> fe2["pages/ScanPage.jsx — upload → pipeline"]
    fe --> fe3["pages/AnalysisPage.jsx — results + schemes"]
    fe --> fe4["pages/CropCalendarPage.jsx"]
    fe --> fe5["pages/YieldEstimatorPage.jsx"]
    fe --> fe6["pages/GeoMapPage.jsx"]
    fe --> fe7["pages/HistoryPage.jsx"]
    fe --> fe8["pages/ChatPage.jsx — RaithuMitra"]

    be --> be1["app.py — API routes"]
    be --> be2["pipeline.py — ML pipeline"]
    be --> be3["leaf_validator.py — face/leaf gating"]
    be --> be4["schemes_data.py — 13 govt schemes"]
    be --> be5["models/ — .keras + .pkl weights"]

    infra --> in1["cloudformation.yaml — ECR + S3 + IAM"]
```

---

## 🏗️ Deployment

Full walkthrough: **[`DEPLOY.md`](./DEPLOY.md)** · One-command foundation stack: **[`infra/cloudformation.yaml`](./infra/cloudformation.yaml)**

```mermaid
flowchart LR
    A[1️⃣ Deploy foundation stack<br/>aws cloudformation deploy] --> B[2️⃣ Upload model weights<br/>aws s3 sync backend/models → S3]
    B --> C[3️⃣ Build & push Docker image<br/>docker build → ECR]
    C --> D[4️⃣ Create ECS Express Mode service<br/>point at ECR image + S3 bucket]
    D --> E[5️⃣ Deploy frontend to Vercel<br/>point VITE_API_URL at ECS URL]
    E --> F[✅ Live app]
```

Stack: **Amazon ECS (Fargate, Express Mode)** for the backend container · **Vercel** for the frontend · **S3** for uploads, scan history, and model weights · **ECR** for the Docker image.

---

## 🧠 Patent-Style Features

- Multi-modal leaf disease detection (image + environmental context)
- Reinforcement-learning recommendation engine
- Geo-intelligence outbreak prediction
- 7-day disease progression forecasting
- Adaptive weight feedback loop (auto-retraining)
- Treatment comparison with value scoring
- Explainability (XAI) factors surfaced per diagnosis
- Automated end-to-end decision pipeline
- Crop-matched government scheme surfacing
- Crop calendar with disease-risk overlay
