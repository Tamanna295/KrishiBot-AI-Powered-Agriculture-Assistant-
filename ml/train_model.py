"""
train_model.py -- Train a RandomForest crop recommendation model
Run this once:  python ml/train_model.py
Outputs: ml/crop_model.pkl, ml/scaler.pkl, ml/label_encoder.pkl
"""

import os
import sys
import io
import pickle
import pandas as pd

# Fix Windows console Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "datasets", "Crop_recommendation.csv")
ML_DIR = os.path.dirname(os.path.abspath(__file__))

def train():
    print("[*] Loading dataset...")
    df = pd.read_csv(DATA)
    print(f"    Rows: {len(df)}, Crops: {df['label'].nunique()}")

    # Features & target
    FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    X = df[FEATURES].values
    y = df["label"].values

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    print("[*] Training Random Forest (200 trees)...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Feature importance
    fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("\nFeature Importance:")
    for feat, imp in fi.items():
        bar = "█" * int(imp * 40)
        print(f"   {feat:<15} {bar} {imp:.3f}")

    # Save artifacts
    with open(os.path.join(ML_DIR, "crop_model.pkl"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(ML_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(ML_DIR, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)
    with open(os.path.join(ML_DIR, "feature_names.pkl"), "wb") as f:
        pickle.dump(FEATURES, f)

    print(f"\nModel saved -> ml/crop_model.pkl")
    print(f"Scaler saved -> ml/scaler.pkl")
    print(f"Labels saved -> ml/label_encoder.pkl")
    print(f"\nTraining complete! Accuracy: {acc*100:.1f}%")
    return acc

if __name__ == "__main__":
    train()
