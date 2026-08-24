# SatInsight AI
**AI-powered Satellite Data Analysis Platform**
*IBM AI Builders Challenge — August 2026*

---

## Overview

SatInsight AI transforms complex satellite telemetry data into clear, actionable insights using AI/ML. Upload a CSV of satellite telemetry (or load the bundled sample dataset) and get anomaly detection, interactive charts, AI-generated explanations, and recommended actions — all in a space-themed dashboard.

## Architecture

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| State | Zustand |
| Charts | Recharts |
| Backend | FastAPI (Python 3.11+) |
| Data processing | Pandas |
| Anomaly detection | Scikit-learn — Isolation Forest + Z-Score |
| AI explanations | Rule-based template engine (IBM Watson slot available) |

---

## Prerequisites

- **Python 3.11+** (Python 3.14 tested; pydantic pre-release required for 3.14)
- **Node.js 18+** and npm

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/your-org/satinsight-ai.git
cd satinsight-ai
```

### 2. Start the backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
# Note: Python 3.14 users need pydantic pre-release (installed automatically)
pip install --pre pydantic pydantic-settings
pip install -r requirements.txt

# Copy env file (optional — defaults work for local dev)
cp .env.example .env

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at **http://localhost:8000**
Swagger API docs at **http://localhost:8000/docs**

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

> The Vite dev server proxies `/api` requests to `http://localhost:8000` automatically.

---

## Sample Dataset

`backend/data/sample_satellite.csv` — 600 rows of synthetic satellite telemetry with **10 injected anomaly windows**:

| Rows | Event | Severity |
|---|---|---|
| 80–82 | Solar flare (radiation spike) | Critical |
| 140–155 | Thermal runaway | Critical |
| 200–215 | Battery drain event | Critical |
| 260–268 | Signal loss | Warning |
| 310–313 | Pressure drop | Critical |
| 370–372 | Velocity spike | Critical |
| 420–425 | Altitude drop | Warning |
| 480–483 | Combined sensor anomaly | Warning |
| 530 | Isolated temperature spike | Critical |
| 560 | Isolated battery critical | Critical |

**Parameters:** `timestamp`, `temperature`, `radiation`, `pressure`, `battery_level`, `signal_strength`, `velocity`, `altitude`

---

## MVP Build Phases

| Phase | Sub-Task | Status |
|---|---|---|
| 1 | Project Scaffolding + Sample Data | ✅ Complete |
| 2 | Backend Core: Data Processing + API Endpoints | ⏳ Pending |
| 3 | AI/ML Core: Anomaly Detection + Insight Generation | ⏳ Pending |
| 4 | Frontend Core: Layout, State, API Client | ⏳ Pending |
| 5 | Frontend Features: Charts, Tables, All Pages | ⏳ Pending |
| 6 | Integration, Polish, and Report Endpoint | ⏳ Pending |

---

## Project Structure

```
satinsight-ai/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   ├── routes/              # data, analysis, anomalies, insights, reports
│   │   └── models/              # Pydantic schemas
│   ├── core/                    # config, session store, exceptions
│   ├── services/                # data_processor, anomaly_detector, insight_generator, report_builder
│   └── data/
│       └── sample_satellite.csv
└── frontend/
    └── src/
        ├── pages/               # 6 page components (Sub-Task 4+)
        ├── components/          # charts, tables, ui primitives (Sub-Task 4+)
        ├── store/               # Zustand store (Sub-Task 4+)
        └── api/                 # Axios client (Sub-Task 4+)
```

---

## Future Integration Points

- **NASA Open APIs** (DONKI, EONET) → `backend/services/nasa_adapter.py`
- **IBM Watson NLP** → swap `insight_generator.py` with Watson NLU API
- **OpenAI GPT** → same swap, same response schema
- **Real-time streaming** → Redis + WebSocket
- **PostgreSQL + TimescaleDB** → replace in-memory session

---

## License

MIT — see [LICENSE](LICENSE)
