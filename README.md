#  Energy AI Platform v2

> Full-stack AI-powered platform for energy consumption **forecasting**, **anomaly detection**,
> **optimization** and **scenario simulation**.

---

##  Quick Start (Local — VSCode / Terminal)

### Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.9 + | https://python.org |
| Node.js | 18 + | https://nodejs.org |
| npm | 9 + | bundled with Node.js |

---

### Step 1 — Backend

Open a terminal in the `energy-ai-pro/` folder:

```bash
# 1. Enter the backend directory
cd backend

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
#    Windows:
venv\Scripts\activate
#    Mac / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the API server  ← run from inside backend/
uvicorn main:app --reload --port 8000
```

> ✅ Backend running at **http://localhost:8000**
> 📖 Swagger docs at **http://localhost:8000/docs**

---

### Step 2 — Frontend

Open a **second** terminal in the `energy-ai-pro/` folder:

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Install npm packages (first run only — takes ~30 sec)
npm install

# 3. Start the dev server
npm run dev
```

> ✅ Frontend running at **http://localhost:3000**

---

### One-command start (Mac / Linux)

```bash
chmod +x start.sh && ./start.sh
```

### One-command start (Windows)

```bat
start.bat
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## 📁 Getting Started (in the app)

1. Open **http://localhost:3000**
2. Click **Upload Data** in the sidebar
3. Click **"Generate 6-Month Sample Dataset"** — no file needed
4. Explore **Dashboard → Forecast → Anomaly → Optimization → Simulation**

Or upload your own CSV with columns: `timestamp`, `energy_kwh`
(optional: `device_id`, `building_id`, `temperature`, `humidity`, `occupancy`)

---

## 🗂️ Project Structure

```
energy-ai-pro/
├── backend/
│   ├── main.py                    ← Entry point (uvicorn main:app)
│   ├── requirements.txt
│   ├── .env.example               ← Copy to .env to configure
│   ├── Dockerfile
│   └── app/
│       ├── main.py                ← FastAPI application factory
│       ├── database.py            ← SQLAlchemy ORM (SQLite)
│       ├── core/
│       │   ├── config.py          ← pydantic-settings
│       │   ├── exceptions.py      ← Typed error classes + handlers
│       │   └── logging.py         ← Structured logging
│       ├── models/
│       │   └── schemas.py         ← 40+ Pydantic v2 schemas
│       ├── ml/
│       │   ├── forecasting.py     ← ARIMA + Ridge Regression
│       │   ├── anomaly.py         ← Isolation Forest + Z-Score
│       │   ├── optimization.py    ← 8 recommendation categories
│       │   └── simulation.py      ← 4 scenario engines
│       ├── services/
│       │   ├── data_store.py      ← Singleton DataFrame store
│       │   ├── alert_service.py   ← Alert CRUD business logic
│       │   └── export_service.py  ← CSV / JSON export
│       ├── api/v1/
│       │   ├── router.py          ← Mounts all 11 routers
│       │   └── endpoints/
│       │       ├── upload.py      ← POST /upload/csv, /generate-sample
│       │       ├── dashboard.py   ← GET /dashboard/summary, /historical, ...
│       │       ├── forecast.py    ← POST /forecast/run, /batch
│       │       ├── anomaly.py     ← POST /anomaly/run
│       │       ├── optimization.py← GET /optimization/recommendations
│       │       ├── simulation.py  ← POST /simulation/run
│       │       ├── alerts.py      ← Full CRUD /alerts/
│       │       ├── devices.py     ← GET /devices/, /devices/{id}
│       │       ├── reports.py     ← GET /reports/export/csv, /json
│       │       ├── models_compare.py ← GET /models/compare
│       │       └── health.py      ← GET /health/detailed, /metrics
│       └── utils/
│           ├── preprocessing.py   ← Clean, validate, fill gaps
│           └── data_generator.py  ← Synthetic 6-month dataset
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx                ← Router + sidebar layout + context
│       ├── index.css              ← Full dark design system
│       ├── services/api.js        ← All 49 API calls (axios)
│       ├── components/ui.jsx      ← Shared: KpiCard, DataTable, Alert, ...
│       └── pages/
│           ├── DashboardPage.jsx
│           ├── ForecastPage.jsx
│           ├── AnomalyPage.jsx
│           ├── OptimizationPage.jsx
│           ├── SimulationPage.jsx
│           ├── DevicesPage.jsx
│           ├── AlertsPage.jsx
│           ├── ReportsPage.jsx
│           ├── ModelsPage.jsx
│           └── UploadPage.jsx
│
├── docker-compose.yml
├── start.sh                       ← Mac/Linux one-command start
├── start.bat                      ← Windows one-command start
└── README.md
```

---

## 🌐 API Reference (49 Endpoints)

Base URL: `http://localhost:8000/api/v1`
Interactive docs: `http://localhost:8000/docs`

### 📁 Upload
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/csv` | Upload energy CSV file |
| POST | `/upload/generate-sample` | Generate synthetic sample data |
| GET | `/upload/status` | Check loaded dataset |
| DELETE | `/upload/clear` | Clear all data |

### 📊 Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | All KPIs (cost, trend, forecast, alerts) |
| GET | `/dashboard/historical` | Time-series data with filter + resolution |
| GET | `/dashboard/device-breakdown` | Per-device share and cost |
| GET | `/dashboard/hourly-pattern` | 24-hour average load profile |
| GET | `/dashboard/weekly-pattern` | Mon–Sun average profile |
| GET | `/dashboard/monthly-trend` | Month-by-month aggregation |
| GET | `/dashboard/cost-analysis` | Peak vs off-peak cost breakdown |
| GET | `/dashboard/statistics` | Descriptive stats (percentiles, skew) |

### 📈 Forecast
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/forecast/run` | Run single device forecast |
| POST | `/forecast/batch` | Forecast multiple devices at once |
| GET | `/forecast/quick/{horizon}` | Quick all-device forecast |
| GET | `/forecast/devices` | List available devices |

### 🔍 Anomaly
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/anomaly/run` | Run anomaly detection |
| GET | `/anomaly/quick` | Quick scan with defaults |
| GET | `/anomaly/summary` | Fast stats without full scan |
| GET | `/anomaly/methods` | List available methods |

### 💡 Optimization
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/optimization/recommendations` | AI recommendations with savings |
| GET | `/optimization/peak-analysis` | Peak hour breakdown |
| GET | `/optimization/savings-summary` | Quick savings potential |
| GET | `/optimization/device-stats` | Device consumption stats |

### 🔬 Simulation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulation/run` | Run scenario simulation |
| GET | `/simulation/scenarios` | List scenarios + parameters |
| GET | `/simulation/history` | Past simulation runs |

### 🔔 Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/alerts/` | List alerts (filterable) |
| POST | `/alerts/` | Create manual alert |
| GET | `/alerts/counts` | Total / unread / by severity |
| GET | `/alerts/{id}` | Get single alert |
| PATCH | `/alerts/{id}/read` | Mark as read |
| PATCH | `/alerts/{id}/resolve` | Resolve alert |
| POST | `/alerts/mark-all-read` | Bulk mark read |
| DELETE | `/alerts/{id}` | Delete alert |

### 🖥️ Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/devices/` | All devices with stats |
| GET | `/devices/{id}` | Device detail + hourly/weekly profile |
| GET | `/devices/{id}/forecast` | Device-specific forecast |
| GET | `/devices/{id}/anomalies` | Device anomaly report |
| GET | `/devices/{id}/history` | Device historical readings |

### 📄 Reports & Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/summary` | Full JSON summary report |
| GET | `/reports/export/csv` | Download raw dataset as CSV |
| GET | `/reports/export/report-csv` | Download report as CSV |
| GET | `/reports/export/json` | Download report as JSON |

### 🤖 Models
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models/compare` | Side-by-side ARIMA vs Linear |
| GET | `/models/accuracy-history` | Past accuracy measurements |

### ❤️ Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Basic health ping |
| GET | `/health/detailed` | DB + data store status |
| GET | `/health/metrics` | API usage counters |

---

## 🧠 ML Architecture

### Forecasting
- **ARIMA** (default): fitted on last 90 days of daily totals, expanded to hourly using a 24-point load profile. Provides 95% confidence intervals.
- **Ridge Regression** (fallback): 9 cyclical time features (sin/cos of hour, day, month + weekend + night flags). Trained on last 60 days.
- **Metrics**: MAE, RMSE, Accuracy % (100 − MAPE)

### Anomaly Detection
- **Isolation Forest**: 200 trees, multivariate (energy + time + rolling stats)
- **Z-Score**: rolling 24-hour window, flags |z| > 3
- **Ensemble**: OR of both — highest recall
- **Types detected**: consumption spike · sudden drop · night spike · extreme deviation · statistical anomaly

### Optimization Engine
8 recommendation categories with estimated kWh + USD savings:
Load Balancing · Scheduling · Device Optimisation · Fault Detection · HVAC · Weekend Setback · Battery/Off-peak · Lighting

### Simulation Scenarios
| Scenario | Model |
|----------|-------|
| Occupancy Change | Linear occupancy-to-load sensitivity model |
| Temperature Change | ~3%/°C HVAC load adjustment (ASHRAE benchmark) |
| Device Shutdown | Hourly load subtraction during shutdown window |
| Peak Reduction | Demand-response clipping on top N% of hours |

---

## ⚙️ Configuration

Copy `.env.example` to `.env` in the `backend/` folder:

```env
APP_ENV=development
DEBUG=true
DATABASE_URL=sqlite:///./energy_platform.db
ELECTRICITY_RATE_USD_KWH=0.12
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install pytest
pytest tests/test_ml.py -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI 0.104, Uvicorn |
| ML | scikit-learn 1.3, statsmodels 0.14, NumPy, pandas |
| Database | SQLite via SQLAlchemy 2.0 ORM |
| Frontend | React 18, Vite 5, React Router 6 |
| Charts | Recharts 2.10 |
| Icons | Lucide React |
| HTTP Client | Axios |
| Containers | Docker + Compose + Nginx |

---

## ❓ Common Issues

| Problem | Fix |
|---------|-----|
| `Could not import module "main"` | Make sure you are inside `backend/` folder before running uvicorn |
| `npm run dev` fails | Run `npm install` first inside `frontend/` |
| CORS error in browser | Confirm backend is running on port 8000 |
| `No data loaded` banner | Go to Upload page → Generate Sample Data |
| Forecast fails with < 48 records | Upload more data or use the sample generator |
#   A I - B a s e d - e n e r g y - c o n s u m p t i o n - f o r e c a s t i n g . 
 
 
