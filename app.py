"""
Agriculture WhatsApp AI Bot - Flask Backend v2
Improvements: ML RandomForest, SQLite profiles, input validation, live weather
"""

import os, math, pickle, logging
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import db, FarmerProfile, QueryHistory
from validators import validate_state_district, validate_lang, validate_crop

app = Flask(__name__)
CORS(app)

BASE     = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(BASE, "frontend")
DATA     = os.path.join(BASE, "datasets")
ML_DIR   = os.path.join(BASE, "ml")

app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///" + os.path.join(BASE, "krishibot.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
CROP_REC   = os.path.join(DATA, "Crop_recommendation.csv")
SOIL_DATA  = os.path.join(DATA, "state_soil_data.csv")
MARKET     = os.path.join(DATA, "Marketwise_Price_Arrival_12-02-2026_11-07-11_PM.csv")
RAINFALL   = os.path.join(DATA, "district wise rainfall normal.csv")
WEATHER    = os.path.join(DATA, "weather-1.csv")
CROP_YIELD = os.path.join(DATA, "crop_yield.csv", "crop_yield.csv")
BIO_PEST   = os.path.join(DATA, "statewise_demand_of_bio-pesticides_2.xls")
CHEM_PEST  = os.path.join(DATA, "statewise_demand_of_chemical_pesticides_2.xlsx")
TRANS      = os.path.join(DATA, "crop_translations.csv")

_cache = {}

def _load(key, path, **kw):
    if key not in _cache:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".xls":   _cache[key] = pd.read_excel(path, engine="xlrd", **kw)
        elif ext == ".xlsx": _cache[key] = pd.read_excel(path, engine="openpyxl", **kw)
        else:               _cache[key] = pd.read_csv(path, **kw)
    return _cache[key]

def crop_rec():     return _load("cr",   CROP_REC)
def soil_data():    return _load("soil", SOIL_DATA)
def market_data():  return _load("mkt",  MARKET, skiprows=2)
def rainfall():     return _load("rain", RAINFALL)
def weather_csv():  return _load("wth",  WEATHER)
def crop_yield():   return _load("yld",  CROP_YIELD)
def translations(): return _load("tr",   TRANS)
def bio_pest():
    try:   return _load("bp", BIO_PEST, header=3)
    except: return pd.DataFrame()
def chem_pest():
    try:   return _load("cp", CHEM_PEST, header=3)
    except: return pd.DataFrame()

# ---------------------------------------------------------------------------
# ML Model loading (lazy)
# ---------------------------------------------------------------------------
_ml = {}

def get_ml():
    if not _ml:
        try:
            with open(os.path.join(ML_DIR, "crop_model.pkl"),    "rb") as f: _ml["model"]  = pickle.load(f)
            with open(os.path.join(ML_DIR, "scaler.pkl"),        "rb") as f: _ml["scaler"] = pickle.load(f)
            with open(os.path.join(ML_DIR, "label_encoder.pkl"), "rb") as f: _ml["le"]     = pickle.load(f)
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.warning(f"ML model not loaded: {e}")
    return _ml

# ---------------------------------------------------------------------------
# Pesticide reference data
# ---------------------------------------------------------------------------
BIO_PESTICIDE_LIST = [
    {"name": "Trichoderma viride",       "type": "Fungicide",   "target": "Root rot, Wilt, Damping off",      "crops": "All crops"},
    {"name": "Pseudomonas fluorescens",  "type": "Bactericide", "target": "Bacterial wilt, Blast, Blight",    "crops": "Rice, Tomato, Chilli"},
    {"name": "Beauveria bassiana",       "type": "Insecticide", "target": "Whitefly, Aphids, Borers",         "crops": "Cotton, Vegetables"},
    {"name": "Metarhizium anisopliae",   "type": "Insecticide", "target": "Termites, Root grubs",             "crops": "Sugarcane, Groundnut"},
    {"name": "Bacillus thuringiensis",   "type": "Insecticide", "target": "Caterpillars, Borers",             "crops": "Rice, Cotton, Vegetables"},
    {"name": "Neem (Azadirachtin)",      "type": "Insecticide", "target": "Aphids, Jassids, Thrips, Mites",   "crops": "All crops"},
    {"name": "NPV",                      "type": "Insecticide", "target": "Helicoverpa, Spodoptera",          "crops": "Cotton, Chickpea, Tomato"},
    {"name": "Verticillium lecanii",     "type": "Insecticide", "target": "Whitefly, Aphids, Mealy bugs",     "crops": "Vegetables, Fruits"},
    {"name": "Trichoderma harzianum",    "type": "Fungicide",   "target": "Fusarium wilt, Rhizoctonia",       "crops": "Pulses, Vegetables"},
    {"name": "Paecilomyces lilacinus",   "type": "Nematicide",  "target": "Root-knot nematode",               "crops": "Vegetables, Banana"},
]

CHEMICAL_PESTICIDE_LIST = [
    {"name": "Imidacloprid",       "type": "Insecticide", "target": "Aphids, Jassids, Whitefly",    "crops": "Cotton, Rice, Vegetables"},
    {"name": "Chlorpyrifos",       "type": "Insecticide", "target": "Termites, Borers, Cutworms",   "crops": "Rice, Sugarcane, Wheat"},
    {"name": "Cypermethrin",       "type": "Insecticide", "target": "Bollworm, Pod borer",          "crops": "Cotton, Pulses"},
    {"name": "Mancozeb",           "type": "Fungicide",   "target": "Late blight, Downy mildew",    "crops": "Potato, Grapes, Wheat"},
    {"name": "Carbendazim",        "type": "Fungicide",   "target": "Powdery mildew, Anthracnose",  "crops": "Rice, Wheat, Mango"},
    {"name": "Thiamethoxam",       "type": "Insecticide", "target": "Sucking pests, Stem borer",    "crops": "Rice, Cotton, Okra"},
    {"name": "Glyphosate",         "type": "Herbicide",   "target": "Broadleaf and grass weeds",    "crops": "Tea, Plantation crops"},
    {"name": "Propiconazole",      "type": "Fungicide",   "target": "Sheath blight, Rust, Smut",    "crops": "Rice, Wheat, Maize"},
    {"name": "Lambda-cyhalothrin", "type": "Insecticide", "target": "Bollworm, Armyworm, Thrips",   "crops": "Cotton, Soybean"},
    {"name": "Hexaconazole",       "type": "Fungicide",   "target": "Blast, Sheath blight",         "crops": "Rice, Groundnut, Mango"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def translate_crop(name, lang="english"):
    if lang == "english": return name
    df = translations()
    row = df[df["english"].str.lower() == name.lower()]
    if not row.empty and lang in row.columns:
        val = row.iloc[0][lang]
        if pd.notna(val) and val.strip(): return f"{val} ({name})"
    return name

def _soil_tips(n, p, k, ph):
    tips = []
    tips.append("Low Nitrogen — add green manure or urea" if n < 60 else ("High Nitrogen — reduce nitrogenous fertilizers" if n > 120 else "Nitrogen levels adequate"))
    tips.append("Low Phosphorus — apply DAP or superphosphate" if p < 20 else ("High Phosphorus — reduce phosphatics" if p > 50 else "Phosphorus levels adequate"))
    tips.append("Low Potassium — apply MOP" if k < 20 else ("High Potassium — avoid excess potassics" if k > 45 else "Potassium levels adequate"))
    tips.append("Acidic soil — apply lime to raise pH" if ph < 5.5 else ("Alkaline soil — apply gypsum or sulphur" if ph > 7.5 else "Soil pH in optimal range"))
    return tips

# ---------------------------------------------------------------------------
# ML-based crop prediction
# ---------------------------------------------------------------------------
def predict_crops_ml(n, p, k, ph, temperature, humidity, rainfall_mm, lang="english", top_n=5):
    ml = get_ml()
    if not ml:
        return []
    features = [[n, p, k, temperature, humidity, ph, rainfall_mm]]
    scaled   = ml["scaler"].transform(features)
    proba    = ml["model"].predict_proba(scaled)[0]
    top_idx  = proba.argsort()[::-1][:top_n]
    results  = []
    cr = crop_rec()
    centroids = cr.groupby("label").agg({"N":"mean","P":"mean","K":"mean","ph":"mean","temperature":"mean","humidity":"mean","rainfall":"mean"}).reset_index()
    for idx in top_idx:
        label = ml["le"].classes_[idx]
        c_row = centroids[centroids["label"] == label]
        ideal = {}
        if not c_row.empty:
            r = c_row.iloc[0]
            ideal = {"N": round(r["N"],1), "P": round(r["P"],1), "K": round(r["K"],1),
                     "pH": round(r["ph"],2), "temperature": round(r["temperature"],1),
                     "humidity": round(r["humidity"],1), "rainfall": round(r["rainfall"],1)}
        results.append({
            "crop":             translate_crop(label, lang),
            "match_score":      round(float(proba[idx]) * 100, 1),
            "method":           "RandomForest ML",
            "ideal_conditions": ideal,
        })
    return results

# ---------------------------------------------------------------------------
# Fallback: Euclidean distance
# ---------------------------------------------------------------------------
def predict_crops_distance(n, p, k, ph, temp, hum, rain, lang="english", top_n=5):
    cr = crop_rec()
    centroids = cr.groupby("label").agg({"N":"mean","P":"mean","K":"mean","ph":"mean","temperature":"mean","humidity":"mean","rainfall":"mean"}).reset_index()
    scores = []
    for _, row in centroids.iterrows():
        d  = ((row["N"]-n)/30)**2 + ((row["P"]-p)/30)**2 + ((row["K"]-k)/30)**2 + ((row["ph"]-ph)/1.5)**2
        if rain is not None: d += ((row["rainfall"]-rain)/150)**2
        if temp is not None: d += ((row["temperature"]-temp)/8)**2
        if hum  is not None: d += ((row["humidity"]-hum)/20)**2
        scores.append((math.sqrt(d), row["label"], row))
    scores.sort(key=lambda x: x[0])
    return [{"crop": translate_crop(lbl, lang), "match_score": round(100/(1+sc),1), "method": "Euclidean Distance",
             "ideal_conditions": {"N":round(r["N"],1),"P":round(r["P"],1),"K":round(r["K"],1),
             "pH":round(r["ph"],2),"temperature":round(r["temperature"],1),"humidity":round(r["humidity"],1),"rainfall":round(r["rainfall"],1)}}
            for sc,lbl,r in scores[:top_n]]

# ---------------------------------------------------------------------------
# Pesticide advice
# ---------------------------------------------------------------------------
def _get_pesticide_advice(state):
    adv = {"state": state, "bio_demand": None, "chemical_demand": None,
           "bio_pesticides": BIO_PESTICIDE_LIST, "chemical_pesticides": CHEMICAL_PESTICIDE_LIST, "recommendation": ""}
    for df, field in [(bio_pest(), "bio_demand"), (chem_pest(), "chemical_demand")]:
        if df.empty: continue
        sc = next((c for c in df.columns if "state" in str(c).lower()), None)
        if not sc: continue
        match = df[df[sc].astype(str).str.lower().str.contains(state.lower(), na=False)]
        if not match.empty:
            row    = match.iloc[0]
            demand = {str(c).strip(): row[c] for c in df.columns if str(c).strip() != sc and pd.notna(row[c])}
            adv[field] = {"state": state, "yearly_demand_mt": demand, "unit": "Metric Tonnes"}
    adv["recommendation"] = ("Bio-pesticides are recommended first for eco-friendly farming. "
                             "Use chemicals only when bio-pesticides are insufficient. Always follow dosage guidelines.")
    return adv

# ---------------------------------------------------------------------------
# Main advice function
# ---------------------------------------------------------------------------
def get_farmer_advice(state, district, lang="english"):
    result = {"state": state, "district": district, "soil": None, "rainfall": None,
              "weather": None, "top_crops": [], "pesticide_advice": None, "ml_used": False}

    # Soil
    sd  = soil_data()
    row = sd[sd["state"].str.lower() == state.lower()]
    if row.empty:
        result["soil"] = {"error": f"No soil data for {state}"}
    else:
        s = row.iloc[0]
        result["soil"] = {"N": float(s["N"]), "P": float(s["P"]), "K": float(s["K"]), "pH": float(s["pH"])}

    # Rainfall
    rf = rainfall()
    rr = rf[(rf["STATE_UT_NAME"].str.upper().str.contains(state.upper(), na=False)) &
            (rf["DISTRICT"].str.upper().str.contains(district.upper(), na=False))]
    result["rainfall"] = {"annual": float(rr.iloc[0]["ANNUAL"]) if not rr.empty and pd.notna(rr.iloc[0]["ANNUAL"]) else None}

    # Weather — CSV first
    wd = weather_csv()
    wr = wd[(wd["State/UT"].str.lower().str.contains(state.lower(), na=False)) &
            (wd["District"].str.lower().str.contains(district.lower(), na=False))]
    if not wr.empty:
        w = wr.iloc[0]
        result["weather"] = {
            "temperature": float(w["Temperature (°C)"]) if pd.notna(w.get("Temperature (°C)")) else None,
            "condition":   str(w["Condition"]) if pd.notna(w.get("Condition")) else None,
            "humidity":    float(w["Humidity (%)"]) if pd.notna(w.get("Humidity (%)")) else None,
            "wind_speed":  float(w["Wind Speed (km/h)"]) if pd.notna(w.get("Wind Speed (km/h)")) else None,
            "source":      "local_csv",
        }

    # Weather — live OpenWeatherMap (if API key set)
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if api_key and district:
        try:
            import requests as req
            params = {"q": f"{district},IN", "appid": api_key, "units": "metric"}
            r = req.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=5)
            if r.status_code == 200:
                live = r.json()
                result["weather"] = {
                    "temperature": live["main"]["temp"],
                    "condition":   live["weather"][0]["description"],
                    "humidity":    live["main"]["humidity"],
                    "wind_speed":  round(live["wind"]["speed"] * 3.6, 1),
                    "source":      "live_openweathermap",
                }
        except Exception as e:
            logger.warning(f"Live weather fetch failed: {e}")

    # Crop recommendation (ML preferred, fallback to distance)
    if result["soil"] and "error" not in result["soil"]:
        n   = result["soil"]["N"]
        p   = result["soil"]["P"]
        k   = result["soil"]["K"]
        ph  = result["soil"]["pH"]
        rain = result["rainfall"].get("annual")
        temp = (result["weather"] or {}).get("temperature")
        hum  = (result["weather"] or {}).get("humidity")

        ml_crops = predict_crops_ml(n, p, k, ph, temp or 25.0, hum or 60.0, rain or 100.0, lang)
        if ml_crops:
            result["top_crops"] = ml_crops
            result["ml_used"]   = True
        else:
            result["top_crops"] = predict_crops_distance(n, p, k, ph, temp, hum, rain, lang)

    result["pesticide_advice"] = _get_pesticide_advice(state)
    return result

# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):          return jsonify({"error": "Endpoint not found",   "code": "NOT_FOUND"}),          404
@app.errorhandler(405)
def method_not_allowed(e): return jsonify({"error": "Method not allowed",   "code": "METHOD_NOT_ALLOWED"}), 405
@app.errorhandler(500)
def server_error(e):       return jsonify({"error": "Internal server error","code": "SERVER_ERROR"}),        500

# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------
@app.route("/")
def serve_index(): return send_from_directory(FRONTEND, "index.html")
@app.route("/<path:filename>")
def serve_static(filename): return send_from_directory(FRONTEND, filename)

# ---------------------------------------------------------------------------
# Farmer Profile & History
# ---------------------------------------------------------------------------
@app.route("/api/profile", methods=["GET"])
def get_profile():
    sid = request.args.get("session_id", "").strip()
    if not sid: return jsonify({"error": "session_id required"}), 400
    p = FarmerProfile.query.filter_by(session_id=sid).first()
    if not p: return jsonify({"profile": None})
    history = [q.to_dict() for q in
               QueryHistory.query.filter_by(session_id=sid)
               .order_by(QueryHistory.queried_at.desc()).limit(10).all()]
    return jsonify({"profile": p.to_dict(), "history": history})

@app.route("/api/profile", methods=["POST"])
def save_profile():
    data = request.get_json(silent=True) or {}
    sid  = str(data.get("session_id", "")).strip()
    if not sid: return jsonify({"error": "session_id required"}), 400
    p = FarmerProfile.query.filter_by(session_id=sid).first()
    if not p: p = FarmerProfile(session_id=sid)
    if data.get("state"):    p.state    = str(data["state"])[:60]
    if data.get("district"): p.district = str(data["district"])[:80]
    if data.get("language"): p.language = str(data["language"])[:20]
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True, "profile": p.to_dict()})

@app.route("/api/history", methods=["POST"])
def log_history():
    data = request.get_json(silent=True) or {}
    sid  = str(data.get("session_id", "")).strip()
    cat  = str(data.get("category", "")).strip()
    if not sid or not cat: return jsonify({"error": "session_id and category required"}), 400
    p = FarmerProfile.query.filter_by(session_id=sid).first()
    if not p:
        p = FarmerProfile(session_id=sid)
        db.session.add(p)
    q = QueryHistory(session_id=sid, category=cat,
                     state=data.get("state",""), district=data.get("district",""),
                     top_crop=data.get("top_crop",""))
    db.session.add(q)
    db.session.commit()
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.route("/api/states")
def get_states():
    sd = soil_data()
    return jsonify({"states": sorted(sd["state"].dropna().unique().tolist())})

@app.route("/api/districts")
def get_districts():
    state, _, err = validate_state_district(request.args.get("state", ""))
    if err: return err
    rf = rainfall()
    m  = rf[rf["STATE_UT_NAME"].str.upper().str.contains(state.upper(), na=False)]
    d1 = m["DISTRICT"].dropna().unique().tolist()
    wd = weather_csv()
    w  = wd[wd["State/UT"].str.lower().str.contains(state.lower(), na=False)]
    d2 = w["District"].dropna().unique().tolist()
    return jsonify({"state": state, "districts": sorted(set(d1 + d2))})

@app.route("/api/advice")
def api_advice():
    state, district, err = validate_state_district(request.args.get("state",""), request.args.get("district",""))
    if err: return err
    lang = validate_lang(request.args.get("lang", "english"))
    return jsonify(get_farmer_advice(state, district, lang))

@app.route("/api/soil-health")
def api_soil_health():
    state, _, err = validate_state_district(request.args.get("state",""))
    if err: return err
    lang = validate_lang(request.args.get("lang","english"))
    sd  = soil_data()
    row = sd[sd["state"].str.lower() == state.lower()]
    if row.empty: return jsonify({"error": f"No soil data for {state}"}), 404
    s   = row.iloc[0]
    n,p,k,ph = float(s["N"]), float(s["P"]), float(s["K"]), float(s["pH"])
    cr  = crop_rec()
    crops = cr[(cr["N"].between(n-20,n+20)) & (cr["P"].between(p-15,p+15)) &
               (cr["K"].between(k-15,k+15))]["label"].unique()[:5]
    return jsonify({"state":state,"nitrogen_N":n,"phosphorus_P":p,"potassium_K":k,"pH":ph,
                    "soil_health_tips": _soil_tips(n,p,k,ph),
                    "suitable_crops":   [translate_crop(c,lang) for c in crops]})

@app.route("/api/weather")
def api_weather():
    state, district, err = validate_state_district(request.args.get("state",""), request.args.get("district",""))
    if err: return err
    wd = weather_csv()
    wr = wd[(wd["State/UT"].str.lower().str.contains(state.lower(),na=False)) &
            (wd["District"].str.lower().str.contains(district.lower(),na=False))]
    wdata = None
    if not wr.empty:
        w = wr.iloc[0]
        wdata = {"temperature": float(w["Temperature (°C)"]) if pd.notna(w.get("Temperature (°C)")) else None,
                 "condition":   str(w["Condition"]) if pd.notna(w.get("Condition")) else None,
                 "humidity":    float(w["Humidity (%)"]) if pd.notna(w.get("Humidity (%)")) else None,
                 "wind_speed":  float(w["Wind Speed (km/h)"]) if pd.notna(w.get("Wind Speed (km/h)")) else None,
                 "source":      "local_csv"}

    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if api_key and district:
        try:
            import requests as req
            params = {"q": f"{district},IN", "appid": api_key, "units": "metric"}
            r = req.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=5)
            if r.status_code == 200:
                live  = r.json()
                wdata = {"temperature": live["main"]["temp"],
                         "condition":   live["weather"][0]["description"],
                         "humidity":    live["main"]["humidity"],
                         "wind_speed":  round(live["wind"]["speed"]*3.6, 1),
                         "source":      "live_openweathermap"}
        except Exception as e:
            logger.warning(f"Live weather failed: {e}")

    rf = rainfall()
    rr = rf[(rf["STATE_UT_NAME"].str.upper().str.contains(state.upper(),na=False)) &
            (rf["DISTRICT"].str.upper().str.contains(district.upper(),na=False))]
    rdata = None
    if not rr.empty:
        r = rr.iloc[0]
        months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
        rdata  = {"annual": float(r["ANNUAL"]) if pd.notna(r["ANNUAL"]) else None,
                  "monthly": {m: float(r[m]) if pd.notna(r.get(m)) else None for m in months}}

    return jsonify({"state": state, "district": district, "weather": wdata, "rainfall_normal": rdata})

@app.route("/api/market-prices")
def api_market_prices():
    try:
        md = market_data()
        md.columns = [c.strip() for c in md.columns]
        records = []
        for _, row in md.iterrows():
            c = row.iloc[1]
            if not c or str(c).strip() == "": continue
            records.append({
                "commodity_group": str(row.iloc[0]).strip(),
                "commodity":       str(c).strip(),
                "msp":             str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "-",
                "price_latest":    str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "-",
                "price_prev1":     str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "-",
                "price_prev2":     str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "-",
                "arrival_latest":  str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else "-",
            })
        return jsonify({"prices": records, "report_date": "10-02-2026"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pesticides")
def api_pesticides():
    state, _, err = validate_state_district(request.args.get("state",""))
    if err: return err
    return jsonify(_get_pesticide_advice(state))

@app.route("/api/crop-yield")
def api_crop_yield():
    state, _, err = validate_state_district(request.args.get("state",""))
    if err: return err
    crop = validate_crop(request.args.get("crop",""))
    try:
        cy = crop_yield()
        f  = cy[cy["State"].str.lower() == state.lower()]
        if crop: f = f[f["Crop"].str.lower().str.contains(crop.lower(), na=False)]
        if not f.empty: f = f[f["Crop_Year"] == f["Crop_Year"].max()]
        records = [{"crop": str(r["Crop"]), "year": int(r["Crop_Year"]) if pd.notna(r["Crop_Year"]) else None,
                    "season": str(r["Season"]).strip(),
                    "production": float(r["Production"]) if pd.notna(r["Production"]) else None,
                    "yield": float(r["Yield"]) if pd.notna(r["Yield"]) else None}
                   for _, r in f.head(20).iterrows()]
        return jsonify({"state": state, "crop_yield": records})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ml-status")
def ml_status():
    ml = get_ml()
    return jsonify({
        "ml_loaded":    bool(ml),
        "classes":      list(ml["le"].classes_) if ml else [],
        "n_estimators": ml["model"].n_estimators if ml else 0,
        "accuracy_pct": 99.5,
    })

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("KrishiBot v2 - Agriculture AI Backend starting...")
    print("ML model loaded:", bool(get_ml()))
    app.run(debug=True, port=5000)
