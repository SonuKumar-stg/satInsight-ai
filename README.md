 # SatInsight AI

**AI-powered Satellite Data Analysis Platform**  
*IBM AI Builders Challenge — August 2026*

## Overview

SatInsight AI is an AI/ML-powered satellite telemetry analysis platform that transforms complex satellite data into clear, actionable insights.

Users can upload satellite telemetry data in CSV format or use the bundled sample dataset. The platform performs automated data analysis, anomaly detection, visualization, risk classification, and AI-generated recommendations through a space-themed interactive dashboard.

The platform helps users quickly identify abnormal satellite behaviour across parameters such as temperature, radiation, pressure, battery level, signal strength, velocity, and altitude.

---

## Problem Statement

Satellite telemetry produces large volumes of sensor data that can be difficult to monitor manually.

Important problems such as:

- Thermal abnormalities
- Battery failures
- Radiation spikes
- Signal degradation
- Pressure drops
- Orbital altitude changes
- Unexpected velocity changes
- Multi-sensor failures

may be difficult to identify quickly when analysing raw telemetry data.

SatInsight AI addresses this problem by automatically analysing telemetry data, detecting anomalies, identifying their severity, explaining potential causes, and recommending appropriate actions.

---

## Solution

SatInsight AI provides an end-to-end telemetry analysis workflow:

1. Upload or load satellite telemetry data.
2. Validate and process the dataset.
3. Calculate statistical characteristics of telemetry parameters.
4. Detect anomalies using machine-learning and statistical techniques.
5. Classify detected events as Normal, Warning, or Critical.
6. Identify correlated multi-sensor anomalies.
7. Generate explanations and recommended actions.
8. Display results through interactive charts and tables.
9. Generate a consolidated analysis report.

---

## Key Features

### 📊 Satellite Telemetry Dashboard

- View satellite telemetry data in a structured table.
- Pagination for large datasets.
- Display timestamp, temperature, radiation, pressure, battery, signal, velocity, and altitude.

### 🔍 Anomaly Detection

The platform combines:

- Isolation Forest
- Rolling/statistical Z-score analysis
- Parameter-level anomaly detection
- Multi-sensor correlation

Detected events are classified into:

- 🟢 Normal
- 🟠 Warning
- 🔴 Critical

### 🤖 AI Insights

The system automatically generates explanations for detected anomalies.

Examples include:

- Correlated multi-sensor anomalies
- Elevated thermal readings
- Critical battery levels
- Orbital altitude decay
- Pressure anomalies
- Unexpected velocity changes

Each insight includes:

- Severity
- Affected parameter(s)
- Observed range
- Event rows
- Explanation
- Recommended action

### 📈 Data Analysis

The platform provides statistical analysis including:

- Mean
- Standard deviation
- Minimum
- Maximum
- Quartiles
- Median
- IQR
- Missing-value count

### 📑 Reports

The Reports page provides:

- Session summary
- Total telemetry rows
- Total anomalies
- Risk breakdown
- Parameter statistics
- Analysis status

---

## Architecture

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| State Management | Zustand |
| Charts | Recharts |
| HTTP Client | Axios |
| Backend | FastAPI |
| Language | Python 3.11+ |
| Data Processing | Pandas |
| Machine Learning | Scikit-learn |
| Anomaly Detection | Isolation Forest + Z-score |
| API Documentation | Swagger / OpenAPI |
| AI Insights | Rule-based AI insight generation |

---

## AI / ML Approach

SatInsight AI uses a combination of machine learning and statistical analysis.

### Isolation Forest

Isolation Forest is used to identify unusual telemetry observations by measuring how easily observations can be isolated from the normal data distribution.

### Z-score / Statistical Detection

Statistical analysis is used to identify values that significantly deviate from expected behaviour.

### Multi-Sensor Correlation

The platform also analyses simultaneous anomalies across multiple telemetry parameters.

When several sensors become anomalous during the same time window, the system generates a correlated multi-sensor insight.

This helps identify possible common-cause events such as:

- Power-related failures
- Solar events
- Thermal problems
- Software faults
- Sensor/system failures

---

## AI Insight Generation

The current prototype uses a rule-based AI insight generation layer that converts anomaly patterns into human-readable explanations and recommended actions.

The architecture is designed so that the insight-generation layer can later be connected to external AI services such as IBM Watson or other large language model APIs without changing the core anomaly-detection workflow.

---

## Challenge Theme

SatInsight AI addresses the challenge of using AI to make space exploration and satellite operations more insight-driven.

The project focuses on:

- Helping scientists and engineers understand satellite telemetry.
- Supporting better decision-making in complex environments.
- Converting large volumes of satellite data into actionable insights.
- Detecting potentially dangerous satellite conditions earlier.
- Providing understandable explanations instead of only raw anomaly scores.

---

## How IBM Bob Was Used

IBM Bob was used as the **primary development tool** throughout the development of SatInsight AI.

IBM Bob assisted with:

- Project architecture and planning
- Backend development
- FastAPI route implementation
- Pydantic data models
- Telemetry data processing
- Anomaly detection workflow
- AI insight generation
- React and TypeScript frontend development
- UI component development
- Dashboard implementation
- Charts and data tables
- API integration
- State management using Zustand
- Testing and debugging
- Full-stack integration
- Build validation
- Final application polishing

IBM Bob was used to develop and integrate the backend, frontend, anomaly detection, insight generation, and reporting workflow into a working full-stack prototype.

---

## Validation Results

The completed application was validated through backend tests, frontend builds, and an end-to-end API workflow.

### Backend

- **91/91 backend tests passing**
- All backend API routes registered
- Swagger/OpenAPI documentation available

### Frontend

- TypeScript build completed successfully
- **0 TypeScript errors**
- **0 type warnings**
- 672 modules successfully built

### End-to-End Analysis

Using the sample satellite dataset:

- **600 telemetry rows**
- **106 detected anomalies**
- **494 Normal**
- **80 Warning**
- **26 Critical**
- **10 AI insight cards**

---

 ## Sample Dataset

The bundled dataset is:

`backend/data/sample_satellite.csv`

The dataset contains **600 rows** of synthetic satellite telemetry.

### Telemetry Parameters

- `timestamp`
- `temperature`
- `radiation`
- `pressure`
- `battery_level`
- `signal_strength`
- `velocity`
- `altitude`

### Injected Anomaly Windows

| Rows | Event | Severity |
|---|---|---|
| 80–82 | Solar flare / radiation spike | Critical |
| 140–155 | Thermal runaway | Critical |
| 200–215 | Battery drain event | Critical |
| 260–268 | Signal loss | Warning |
| 310–313 | Pressure drop | Critical |
| 370–372 | Velocity spike | Critical |
| 420–425 | Altitude drop | Warning |
| 480–483 | Combined sensor anomaly | Warning |
| 530 | Isolated temperature spike | Critical |
| 560 | Isolated battery critical | Critical |

---

## Example Analysis Results

The sample dataset produced:

| Risk Level | Count | Percentage |
|---|---:|---:|
| Normal | 494 | 82.3% |
| Warning | 80 | 13.3% |
| Critical | 26 | 4.3% |
| **Total** | **600** | **100%** |

**Total anomalies detected: 106**

---

## Parameter Anomaly Counts

| Parameter | Anomalies |
|---|---:|
| Battery Level | 27 |
| Temperature | 26 |
| Signal Strength | 22 |
| Radiation | 21 |
| Velocity | 17 |
| Altitude | 13 |
| Pressure | 9 |

---

## Example AI Insights

The system can generate insights such as:

### Correlated Multi-Sensor Anomaly

Multiple telemetry parameters can become abnormal simultaneously across consecutive readings.

**Recommended action:** Perform a cross-subsystem health check, review the event timeline, investigate common triggering events, and consider safe-mode operation until the root cause is established.

### Elevated Thermal Readings

A significant temperature increase may indicate solar exposure or thermal-control problems.

**Recommended action:** Review thermal-control telemetry and verify heater/cooler status.

### Critical Battery Level

A severe battery drop may indicate a power-generation problem, excessive subsystem load, or insufficient charge recovery.

**Recommended action:** Reduce non-essential loads and verify solar-panel orientation and power-distribution status.

### Orbital Altitude Decay

A significant altitude decrease may indicate increased atmospheric drag and potential orbital decay.

**Recommended action:** Increase monitoring and evaluate the need for an orbit-maintenance manoeuvre.

---

## Project Structure

```text
satinsight-ai/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   ├── models/
│   │   └── routes/
│   ├── core/
│   ├── services/
│   ├── data/
│   │   └── sample_satellite.csv
│   └── tests/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── api/
        ├── components/
        ├── pages/
        ├── store/
        └── types/
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/SonuKumar-stg/satInsight-ai.git
cd satInsight-ai
```
### 2. Start the Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend: `http://localhost:8000`

Swagger API Documentation: `http://localhost:8000/docs`

### 3. Start the Frontend

Open a new terminal:

```bash
cd satInsight-ai/frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`
 

 
 
