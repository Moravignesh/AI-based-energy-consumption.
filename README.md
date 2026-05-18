<div align="center">

# ⚡ AI-Based Energy Consumption Forecasting & Optimization System

### Full-stack AI platform for energy forecasting, anomaly detection, optimization & scenario simulation

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

</div>

---

## 📌 Overview

The **AI-Based Energy Consumption Forecasting & Optimization System** is a production-ready, full-stack web application that helps organizations predict future energy usage, detect abnormal consumption patterns, generate intelligent cost-saving recommendations, and simulate the impact of operational changes — all powered by machine learning.


### Demo video

frontend demo video : https://drive.google.com/file/d/1mcwNy3YcVVm_z23reiH2THVIiAai6DtQ/view?usp=sharing

backend demo video : https://drive.google.com/file/d/10wOYhzTifImKMDdNS8kbV-IANg_4L66j/view?usp=sharing


---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📈 **Forecasting** | 24h / 7d / 30d predictions using ARIMA & Ridge Regression with confidence intervals |
| 🔍 **Anomaly Detection** | Isolation Forest + Z-Score ensemble detecting 5 anomaly types |
| 💡 **Optimization** | 8 AI-generated recommendation categories with kWh & USD savings estimates |
| 🔬 **Simulation** | 4 scenario engines: occupancy, temperature, device shutdown, peak reduction |
| 📊 **Dashboard** | Real-time KPIs, device breakdown, hourly/weekly/monthly pattern charts |
| 🔔 **Alerts** | Full CRUD alert system with auto-generation from anomaly scans |
| 🖥️ **Device Manager** | Per-device analytics, forecasts, anomaly reports, history |
| 📄 **Reports & Export** | Download raw data and summary reports as CSV or JSON |
| 🤖 **Model Comparison** | Side-by-side ARIMA vs Linear Regression accuracy benchmarking |
| ❤️ **Health API** | Liveness probe, detailed system status, and usage metrics |

---

## 🖼️ Application Pages

| Page | What you see |
|------|-------------|
| Dashboard | KPI cards, consumption trend, device breakdown, hourly pattern chart |
| Forecast | Model selector, confidence band chart, peak alerts, forecast table |
| Anomaly | Time-series with anomalies highlighted, type breakdown, device rates |
| Optimization | Savings KPIs, horizontal bar chart, expandable recommendation cards |
| Simulation | Scenario selector, parameter sliders, baseline vs simulated chart |
| Devices | All devices table, per-device stats, hourly pattern chart |
| Alerts | Filterable alert list, mark read/resolve/delete, severity counts |
| Reports | Summary report, one-click CSV/JSON export buttons |
| Model Compare | Accuracy table, overlay forecast chart, accuracy history log |
| Upload | Drag-and-drop CSV or one-click sample data generation |

---

## 🚀 Quick Start

### Prerequisites

| Tool | Minimum Version | Download |
|------|----------------|----------|
| Python | 3.9+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| Git | any | https://git-scm.com |

---

### 1. Clone the Repository

```bash
git clone https://github.com/Moravignesh/AI-based-energy-consumption..git
cd AI-based-energy-consumption.
```

---

### 2. Start the Backend

```bash
# Enter backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate — Windows:
venv\Scripts\activate

# Activate — Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Start API server (run from inside backend/)
uvicorn main:app --reload --port 8000
```

> ✅ API running at **http://localhost:8000**
> 📖 Swagger docs at **http://localhost:8000/docs**

---

### 3. Start the Frontend

Open a **second terminal**:

```bash
cd frontend
npm install       # first run only
npm run dev
```

> ✅ App running at **http://localhost:3000**

---

### One-Command Start

```bash
# Mac / Linux
chmod +x start.sh && ./start.sh

# Windows
start.bat
```

---

### Docker

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 📁 Getting Started in the App

1. Open **http://localhost:3000**
2. Click **Upload Data** in the sidebar
3. Click **Generate 6-Month Sample Dataset** — no file needed
4. Explore all pages — every feature works with the generated data

### Or upload your own CSV:

| Column | Required | Description |
|--------|----------|-------------|
| `timestamp` | ✅ | ISO 8601 datetime (e.g. `2024-01-01 08:00:00`) |
| `energy_kwh` | ✅ | Energy consumption in kilowatt-hours |
| `device_id` | optional | Meter or device name |
| `building_id` | optional | Building or location grouping |
| `temperature` | optional | Outdoor temperature in °C |
| `humidity` | optional | Relative humidity percentage |
| `occupancy` | optional | Number of occupants |

---

## 🗂️ Project Structure

```
AI-based-energy-consumption./
├── .github/
│   ├── workflows/
│   │   └── ci.yml                   ← GitHub Actions CI pipeline
│   └── pull_request_template.md
│
├── backend/
│   ├── main.py                      ← Entry point: uvicorn main:app
│   ├── requirements.txt             ← Python dependencies
│   ├── .env.example                 ← Environment variable template
│   ├── Dockerfile
│   ├── tests/
│   │   └── test_ml.py               ← pytest unit tests
│   └── app/
│       ├── main.py                  ← FastAPI application factory
│       ├── database.py              ← SQLAlchemy ORM (6 tables)
│       ├── core/
│       │   ├── config.py            ← pydantic-settings configuration
│       │   ├── exceptions.py        ← Custom error classes + handlers
│       │   └── logging.py           ← Structured logging setup
│       ├── models/
│       │   └── schemas.py           ← 40+ Pydantic v2 request/response models
│       ├── ml/
│       │   ├── forecasting.py       ← ARIMA + Ridge Regression engines
│       │   ├── anomaly.py           ← Isolation Forest + Z-Score ensemble
│       │   ├── optimization.py      ← 8 recommendation categories
│       │   └── simulation.py        ← 4 scenario simulation engines
│       ├── services/
│       │   ├── data_store.py        ← Singleton in-memory DataFrame store
│       │   ├── alert_service.py     ← Alert CRUD business logic
│       │   └── export_service.py    ← CSV and JSON export
│       ├── api/v1/
│       │   ├── router.py            ← Mounts all 11 endpoint routers
│       │   └── endpoints/           ← 49 REST API endpoints across 11 files
│       └── utils/
│           ├── preprocessing.py     ← Clean, validate, fill gaps, engineer features
│           └── data_generator.py    ← Synthetic 6-month dataset generator
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── App.jsx                  ← Router + sidebar layout + AppContext
│       ├── index.css                ← Complete dark design system
│       ├── services/
│       │   └── api.js               ← All 49 API calls using axios
│       ├── components/
│       │   └── ui.jsx               ← Shared components: KpiCard, DataTable, etc.
│       └── pages/                   ← 10 full-featured pages
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
├── start.sh                         ← Mac/Linux one-command launcher
├── start.bat                        ← Windows one-command launcher
└── README.md
```

---

## 🌐 API Reference

**Base URL:** `http://localhost:8000/api/v1`
**Interactive Docs:** `http://localhost:8000/docs`

<details>
<summary>📁 Upload — 4 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload/csv` | Upload energy CSV file |
| `POST` | `/upload/generate-sample` | Generate synthetic 6-month data |
| `GET` | `/upload/status` | Check loaded dataset info |
| `DELETE` | `/upload/clear` | Clear all loaded data |

</details>

<details>
<summary>📊 Dashboard — 8 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/summary` | All KPIs (cost, trend, forecast, alerts) |
| `GET` | `/dashboard/historical` | Time-series with device + date filters |
| `GET` | `/dashboard/device-breakdown` | Per-device share and cost |
| `GET` | `/dashboard/hourly-pattern` | 24-hour average load profile |
| `GET` | `/dashboard/weekly-pattern` | Monday–Sunday average profile |
| `GET` | `/dashboard/monthly-trend` | Month-by-month aggregation |
| `GET` | `/dashboard/cost-analysis` | Peak vs off-peak cost breakdown |
| `GET` | `/dashboard/statistics` | Descriptive stats (percentiles, skewness) |

</details>

<details>
<summary>📈 Forecast — 4 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/forecast/run` | Single device forecast (24h/7d/30d) |
| `POST` | `/forecast/batch` | Multi-device batch forecast |
| `GET` | `/forecast/quick/{horizon}` | Quick all-device forecast |
| `GET` | `/forecast/devices` | List available devices |

</details>

<details>
<summary>🔍 Anomaly — 4 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/anomaly/run` | Full anomaly detection run |
| `GET` | `/anomaly/quick` | Quick scan with default settings |
| `GET` | `/anomaly/summary` | Fast stats without full scan |
| `GET` | `/anomaly/methods` | List available detection methods |

</details>

<details>
<summary>💡 Optimization — 4 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/optimization/recommendations` | AI recommendations with savings |
| `GET` | `/optimization/peak-analysis` | Peak hour analysis |
| `GET` | `/optimization/savings-summary` | Quick savings potential |
| `GET` | `/optimization/device-stats` | Per-device consumption stats |

</details>

<details>
<summary>🔬 Simulation — 3 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/simulation/run` | Run scenario simulation |
| `GET` | `/simulation/scenarios` | List scenarios with parameters |
| `GET` | `/simulation/history` | Past simulation runs |

</details>

<details>
<summary>🔔 Alerts — 8 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/alerts/` | List and filter alerts |
| `POST` | `/alerts/` | Create a manual alert |
| `GET` | `/alerts/counts` | Count by total/unread/severity |
| `GET` | `/alerts/{id}` | Get single alert |
| `PATCH` | `/alerts/{id}/read` | Mark alert as read |
| `PATCH` | `/alerts/{id}/resolve` | Resolve an alert |
| `POST` | `/alerts/mark-all-read` | Mark all alerts read |
| `DELETE` | `/alerts/{id}` | Delete an alert |

</details>

<details>
<summary>🖥️ Devices — 5 endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/devices/` | All devices with stats |
| `GET` | `/devices/{id}` | Device detail + patterns |
| `GET` | `/devices/{id}/forecast` | Device-specific forecast |
| `GET` | `/devices/{id}/anomalies` | Device anomaly report |
| `GET` | `/devices/{id}/history` | Device historical readings |

</details>

<details>
<summary>📄 Reports — 4 endpoints · 🤖 Models — 2 · ❤️ Health — 3</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/reports/summary` | Full JSON summary report |
| `GET` | `/reports/export/csv` | Download raw dataset as CSV |
| `GET` | `/reports/export/report-csv` | Download report as CSV |
| `GET` | `/reports/export/json` | Download report as JSON |
| `GET` | `/models/compare` | ARIMA vs Linear Regression comparison |
| `GET` | `/models/accuracy-history` | Past accuracy measurements |
| `GET` | `/health/` | Basic health ping |
| `GET` | `/health/detailed` | Full system status |
| `GET` | `/health/metrics` | API usage counters |

</details>

---

## 🧠 ML Architecture

### Forecasting Models

| Model | Description |
|-------|-------------|
| **ARIMA** | Fitted on last 90 days of daily totals, expanded to hourly using a 24-point load profile. Provides 95% confidence intervals via statsmodels. |
| **Ridge Regression** | 9 cyclical time features (sin/cos of hour, day-of-week, month + weekend + night + business-hour flags). Trained on last 60 days. |

**Metrics reported:** MAE · RMSE · Accuracy % (= 100 − MAPE)

---

### Anomaly Detection

| Method | Algorithm | Best For |
|--------|-----------|----------|
| **Isolation Forest** | 200 trees, multivariate features | Complex multi-dimensional patterns |
| **Z-Score** | Rolling 24h window, \|z\| > 3 | Simple spikes and drops |
| **Ensemble** (default) | IF OR Z-Score | Highest recall — recommended |

**Anomaly types classified:**

| Type | Description |
|------|-------------|
| `consumption_spike` | Energy > 2.5× rolling average |
| `sudden_drop` | Energy < 20% of rolling average |
| `night_spike` | High usage between 10 PM – 6 AM |
| `extreme_deviation` | Z-score > 4σ |
| `statistical_anomaly` | General statistical outlier |

---

### Optimization Engine

Analyses 5 patterns to generate ranked recommendations:

| Pattern Analysed | Recommendation Triggered |
|-----------------|--------------------------|
| Load factor < 0.60 | Shift loads to off-peak hours |
| Night consumption > 15% | Implement overnight shutdown schedule |
| Top device share | Optimise highest-consuming device |
| High device variance | Investigate potential fault/malfunction |
| Weekend reduction < 30% | Enable weekend setback mode |
| HVAC detected | Optimise setpoints + demand ventilation |
| Any off-peak hours | Schedule battery/EV off-peak charging |
| Lighting detected | Upgrade to occupancy-sensor LEDs |

---

### Simulation Scenarios

| Scenario | Physics Model |
|----------|--------------|
| **Occupancy Change** | 30% base load + occupancy-proportional HVAC/lighting sensitivity |
| **Temperature Change** | ~3%/°C HVAC load shift (ASHRAE commercial benchmark) |
| **Device Shutdown** | Hourly load subtraction during configurable shutdown window |
| **Peak Reduction** | Quantile-based demand-response clipping on top N% peak hours |

---

## ⚙️ Configuration

Edit `backend/.env` (copy from `.env.example`):

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
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install pytest
pytest tests/test_ml.py -v
```

Tests cover: preprocessing · forecasting · anomaly detection · optimization · simulation

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11, FastAPI 0.104, Uvicorn |
| ML Libraries | scikit-learn 1.3, statsmodels 0.14, NumPy, pandas |
| Database | SQLite + SQLAlchemy 2.0 ORM |
| Frontend | React 18, Vite 5, React Router 6 |
| Charts | Recharts 2.10 |
| Icons | Lucide React |
| HTTP Client | Axios |
| Containers | Docker + Docker Compose + Nginx |
| CI/CD | GitHub Actions |

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `Could not import module "main"` | Run `uvicorn main:app` from **inside** the `backend/` folder |
| `npm run dev` fails | Run `npm install` first inside `frontend/` |
| CORS error in browser | Confirm backend is running on port 8000 |
| `No data loaded` warning | Go to Upload page → Generate Sample Data |
| Forecast fails with < 48 records | Use the sample data generator |
| Port already in use | Kill existing process or change port |
| `Repository not found` on git push | Check GitHub repo URL and authentication token |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "feat: add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — free to use, modify and distribute.

---

<div align="center">
  <p>Built with ⚡ by <a href="https://github.com/Moravignesh">Moravignesh</a></p>
</div>
