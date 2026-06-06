<<<<<<< HEAD
<![CDATA[# 🌾 KrishiBot — Agriculture WhatsApp AI Bot

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikit-learn)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-Educational-green)]()

> An AI-powered agriculture chatbot that helps Indian farmers make data-driven farming decisions through a WhatsApp-style chat interface. Combines **Machine Learning (RandomForest)** with **Euclidean Distance matching** for crop recommendations, plus soil health analysis, weather data, market prices, pesticide guidance, and multilingual support.

---

## 📸 Screenshots

| Chat Interface | Crop Recommendations | Market Prices |
|:-:|:-:|:-:|
| WhatsApp-style dark UI with sidebar | Top 5 crops with ML confidence scores | 23+ commodities with MSP data |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **ML Crop Prediction** | RandomForest classifier (200 trees, 99.5% accuracy) trained on 2,200 samples across 22 crops |
| 📐 **Euclidean Fallback** | Centroid-based distance matching as fallback when ML model is unavailable |
| 🧪 **Soil Health** | State-wise NPK & pH values with actionable health tips |
| 🌦️ **Weather** | District-level temperature, humidity, wind speed + monthly rainfall bar chart |
| 🌐 **Live Weather** | Optional OpenWeatherMap API integration for real-time weather data |
| 📊 **Market Prices** | Commodity-wise MSP, latest prices, and arrival data for 23+ crops |
| 🛡️ **Pesticide Guide** | 10 bio-pesticides + 10 chemical pesticides with target pests and state-wise demand data |
| 📈 **Crop Yield** | Historical production & yield data by state, year, and season |
| 🌍 **Multilingual** | Crop names in English, Hindi (हिंदी), and Marathi (मराठी) — auto-refreshes on language switch |
| 👤 **Farmer Profiles** | SQLite-backed profiles that remember state/district/language preferences |
| 📜 **Query History** | Tracks past queries per session for personalized experience |
| 🔒 **Input Validation** | Sanitized inputs with proper error codes and messages |
| 🧪 **Unit Tests** | pytest test suite covering soil tips, translation, distance algorithm, and all API endpoints |
| 💬 **NLP Chat** | Keyword-based natural language matching for free-text queries |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Web Browser)                    │
│              http://localhost:5000/                      │
└───────────────────────┬─────────────────────────────────┘
                        │  HTTP Requests (Fetch API)
                        ▼
┌─────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER (frontend/)              │
│                                                          │
│  index.html ─── WhatsApp-style chat layout               │
│  styles.css ─── Dark theme + glassmorphism + animations  │
│  script.js  ─── API calls, rendering, keyword chat       │
└───────────────────────┬─────────────────────────────────┘
                        │  AJAX / Fetch API
                        ▼
┌─────────────────────────────────────────────────────────┐
│              APPLICATION LAYER (app.py)                   │
│                                                          │
│  Flask REST API ──── 11 endpoints (GET + POST)           │
│  validators.py ──── Input sanitization & validation      │
│  database.py   ──── SQLAlchemy models (SQLite)           │
│                                                          │
│  ┌─ ML Engine ──────────────────────────────────┐       │
│  │  RandomForest (200 trees) → predict_proba    │       │
│  │  StandardScaler + LabelEncoder               │       │
│  │  Fallback: Centroid Euclidean Distance        │       │
│  └──────────────────────────────────────────────┘       │
└──────────┬──────────────────────┬───────────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌──────────────────────────┐
│  DATA LAYER      │   │  ML ARTIFACTS (ml/)      │
│  datasets/       │   │                          │
│  9 CSV/Excel     │   │  crop_model.pkl (7.2MB)  │
│  files           │   │  scaler.pkl              │
│                  │   │  label_encoder.pkl        │
└──────────────────┘   └──────────────────────────┘
```

---

## 📁 Project Structure

```
BE project/
├── app.py                          # Flask backend v2 — 11 API endpoints + ML + Euclidean
├── database.py                     # SQLAlchemy models — FarmerProfile, QueryHistory
├── validators.py                   # Input validation & sanitization
├── requirements.txt                # Python dependencies (10 packages)
├── krishibot.db                    # SQLite database (auto-created)
├── README.md                       # This file
│
├── ml/                             # Machine Learning artifacts
│   ├── train_model.py              # Training script — RandomForest (200 trees)
│   ├── crop_model.pkl              # Trained model (7.2 MB)
│   ├── scaler.pkl                  # StandardScaler for feature normalization
│   ├── label_encoder.pkl           # LabelEncoder for crop classes
│   └── feature_names.pkl           # Feature order: N, P, K, temp, humidity, pH, rainfall
│
├── datasets/                       # Agricultural data files
│   ├── Crop_recommendation.csv     # 2,200 rows — N, P, K, temp, humidity, pH, rainfall → label
│   ├── state_soil_data.csv         # 30 states — N, P, K, pH values
│   ├── weather-1.csv               # ~700 districts — temp, humidity, wind, condition
│   ├── district wise rainfall normal.csv  # Monthly + annual rainfall by district
│   ├── Marketwise_Price_Arrival_*.csv     # 23+ commodity prices with MSP
│   ├── crop_yield.csv/             # ~246K rows — historical production data
│   ├── statewise_demand_of_bio-pesticides_2.xls     # Bio-pesticide demand (MT)
│   ├── statewise_demand_of_chemical_pesticides_2.xlsx # Chemical pesticide demand (MT)
│   └── crop_translations.csv       # 34 crops mapped: English → Hindi → Marathi
│
├── frontend/                       # Standalone HTML/CSS/JS (no Node.js needed)
│   ├── index.html                  # WhatsApp-style chat layout
│   ├── styles.css                  # Dark theme, glassmorphism, micro-animations
│   └── script.js                   # API integration, message rendering, NLP chat
│
├── tests/                          # pytest test suite
│   └── test_app.py                 # 20+ unit tests for logic + API endpoints
│
└── .venv/                          # Python virtual environment
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/KrishiBot.git
cd KrishiBot
```

### 2. Set up virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

```bash
python app.py
```

### 5. Open in browser

```
http://localhost:5000/
```

---

## 🔌 API Endpoints

### Data Endpoints

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| GET | `/api/states` | — | List of 30 Indian states |
| GET | `/api/districts` | `state` | Districts for the selected state |
| GET | `/api/advice` | `state`, `district`, `lang` | **Top 5 crops** (ML + fallback) with soil, weather, pesticide advice |
| GET | `/api/soil-health` | `state`, `lang` | NPK/pH values, health tips, suitable crops |
| GET | `/api/weather` | `state`, `district` | Temperature, humidity, condition + monthly rainfall |
| GET | `/api/market-prices` | — | 23+ commodity prices with MSP and arrivals |
| GET | `/api/pesticides` | `state` | Bio/chemical pesticide names + state demand data |
| GET | `/api/crop-yield` | `state`, `crop` (optional) | Historical production and yield data |
| GET | `/api/ml-status` | — | ML model status, accuracy, loaded classes |

### Profile & History Endpoints

| Method | Endpoint | Body / Params | Description |
|--------|----------|---------------|-------------|
| GET | `/api/profile` | `session_id` | Retrieve saved farmer profile + last 10 queries |
| POST | `/api/profile` | `{ session_id, state, district, language }` | Save/update farmer preferences |
| POST | `/api/history` | `{ session_id, category, state, district, top_crop }` | Log a query to history |

### Example Calls

```bash
# Crop advice in Hindi
curl "http://localhost:5000/api/advice?state=Maharashtra&district=Pune&lang=hindi"

# Soil health check
curl "http://localhost:5000/api/soil-health?state=Karnataka"

# Weather + rainfall
curl "http://localhost:5000/api/weather?state=Maharashtra&district=Pune"

# Market prices
curl "http://localhost:5000/api/market-prices"

# Pesticide guide
curl "http://localhost:5000/api/pesticides?state=Maharashtra"

# Crop yield history
curl "http://localhost:5000/api/crop-yield?state=Tamil+Nadu&crop=Rice"

# ML model status
curl "http://localhost:5000/api/ml-status"
```

---

## 🧠 How Crop Recommendation Works

KrishiBot uses a **dual approach** — ML-first with Euclidean fallback:

### Primary: RandomForest ML (99.5% accuracy)

```
Input Features (7):
  N, P, K, pH, temperature, humidity, rainfall
        │
        ▼
  StandardScaler (normalize to zero-mean, unit-variance)
        │
        ▼
  RandomForest Classifier (200 trees)
        │
        ▼
  predict_proba() → probability for each of 22 crops
        │
        ▼
  Top 5 crops by probability (match_score = probability × 100)
```

**Training:** Run `python ml/train_model.py` to retrain the model. It uses 80/20 train-test split with stratified sampling.

### Fallback: Centroid-Based Euclidean Distance

When the ML model is unavailable, the system falls back to computing normalized Euclidean distance:

```
distance = √[
  ((crop_N - local_N) / 30)²  +
  ((crop_P - local_P) / 30)²  +
  ((crop_K - local_K) / 30)²  +
  ((crop_pH - local_pH) / 1.5)²  +
  ((crop_rainfall - local_rainfall) / 150)²  +
  ((crop_temp - local_temp) / 8)²  +
  ((crop_humidity - local_humidity) / 20)²
]

match_score = 100 / (1 + distance)
```

| Feature | Normalization Divisor | Why |
|---------|----------------------|-----|
| N, P, K | 30 | Range ~0–140, gives balanced ~0–4.7 |
| pH | 1.5 | Range ~3.5–10, 1.5 is agriculturally significant |
| Rainfall | 150 | Wide range ~20–300mm, prevents domination |
| Temperature | 8 | Range ~8–44°C, strong crop discriminator |
| Humidity | 20 | Range ~14–100%, moderate weight |

---

## 🌍 Multilingual Support

34 crops mapped across 3 languages in `crop_translations.csv`:

| English | Hindi (हिंदी) | Marathi (मराठी) |
|---------|--------------|----------------|
| rice | चावल | तांदूळ |
| wheat | गेहूं | गहू |
| cotton | कपास | कापूस |
| sugarcane | गन्ना | ऊस |
| coconut | नारियल | नारळ |
| turmeric | हल्दी | हळद |
| mango | आम | आंबा |
| banana | केला | केळे |

The language dropdown auto-refreshes crop recommendations when changed.

---

## 🛡️ Pesticide Reference

### Bio-Pesticides (Recommended First)
| Name | Type | Target Pests |
|------|------|-------------|
| Trichoderma viride | Fungicide | Root rot, Wilt, Damping off |
| Beauveria bassiana | Insecticide | Whitefly, Aphids, Borers |
| Bacillus thuringiensis (Bt) | Insecticide | Caterpillars, Borers |
| Neem (Azadirachtin) | Insecticide | Aphids, Jassids, Thrips, Mites |
| NPV | Insecticide | Helicoverpa, Spodoptera |

### Chemical Pesticides (When Necessary)
| Name | Type | Target Pests |
|------|------|-------------|
| Imidacloprid | Insecticide | Aphids, Jassids, Whitefly |
| Chlorpyrifos | Insecticide | Termites, Borers, Cutworms |
| Mancozeb | Fungicide | Late blight, Downy mildew |
| Cypermethrin | Insecticide | Bollworm, Pod borer |
| Glyphosate | Herbicide | Broadleaf & grass weeds |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- Soil health tip generation (7 tests)
- Crop translation logic (3 tests)
- Euclidean distance prediction (5 tests)
- API endpoint responses (7 tests)
- Input validation (5 tests)

---

## 🔧 Configuration

### Environment Variables (Optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENWEATHER_API_KEY` | Enable live weather from OpenWeatherMap | None (uses CSV data) |

```bash
# To enable live weather:
set OPENWEATHER_API_KEY=your_api_key_here   # Windows
export OPENWEATHER_API_KEY=your_api_key_here # Linux/Mac
```

---

## 🎨 Frontend Design

- **WhatsApp Web–style** dark theme (`#0b141a` background, `#00a884` green accents)
- **Google Fonts** (Inter) for clean typography
- **Glassmorphism** sidebar with `backdrop-filter: blur(20px)`
- **Message bubbles** with fade-in animations and timestamps
- **Data cards** with gradient borders for structured information
- **Crop cards** with rank badges and match percentage scores
- **Mini bar charts** for monthly rainfall visualization
- **Typing indicator** with animated bouncing dots
- **Responsive** — works on desktop and mobile (768px breakpoint)

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework for REST API |
| Flask-CORS | 4.0.0 | Cross-origin resource sharing |
| Flask-SQLAlchemy | 3.1.1 | SQLite ORM for profiles & history |
| SQLAlchemy | 2.0.49 | Database toolkit |
| Pandas | 2.1.4 | CSV/Excel data processing |
| scikit-learn | 1.7.2 | RandomForest ML model |
| openpyxl | 3.1.2 | Read .xlsx Excel files |
| xlrd | 2.0.1 | Read .xls Excel files |
| requests | 2.31.0 | HTTP client (live weather API) |
| pytest | 9.0.3 | Unit testing framework |

---

## 📂 Datasets

| # | File | Records | Key Columns |
|---|------|---------|-------------|
| 1 | `Crop_recommendation.csv` | 2,200 | N, P, K, temp, humidity, pH, rainfall → crop label |
| 2 | `state_soil_data.csv` | 30 | state, N, P, K, pH |
| 3 | `weather-1.csv` | ~700 | State/UT, District, Temperature, Humidity, Wind, Condition |
| 4 | `district wise rainfall normal.csv` | ~700 | STATE_UT_NAME, DISTRICT, JAN–DEC, ANNUAL |
| 5 | `Marketwise_Price_Arrival_*.csv` | 23 | Commodity, MSP, Latest/Previous Prices, Arrivals |
| 6 | `crop_yield.csv` | ~246K | State, District, Crop, Season, Year, Production, Yield |
| 7 | `bio-pesticides_2.xls` | 35+ | States/UTs, yearly demand (Metric Tonnes) |
| 8 | `chemical_pesticides_2.xlsx` | 35+ | States/UTs, yearly demand (Metric Tonnes) |
| 9 | `crop_translations.csv` | 34 | english, hindi, marathi crop names |

---

## 🔮 Future Enhancements

- [ ] **WhatsApp Business API** — Deploy as an actual WhatsApp chatbot
- [ ] **More Languages** — Add Kannada, Tamil, Telugu, Bengali, Gujarati
- [ ] **Deep Learning** — Experiment with neural network crop models
- [ ] **Satellite/Drone Data** — Real-time field health from satellite imagery
- [ ] **SMS/USSD Fallback** — Offline access for farmers without smartphones
- [ ] **User Authentication** — Login-based farmer profiles

---

## 👥 Team

Built as a **Bachelor of Engineering (BE) Final Year Project**.

---

## 📄 License

This project is for educational purposes.
]]>
=======
# KrishiBot-AI-Powered-Agriculture-Assistant-
Built an AI-powered agriculture assistant leveraging Machine Learning, agricultural datasets, and Generative AI to deliver crop recommendations, weather-based insights, market analysis, and personalized farmer assistance.
>>>>>>> ed384fcd83a2a18b1589fd500e745bf988b4b4de
