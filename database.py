"""
database.py — SQLAlchemy models for KrishiBot farmer profiles & query history
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class FarmerProfile(db.Model):
    """
    Stores a farmer's location preferences so they are auto-loaded on return visits.
    Keyed by a browser-generated session_id (stored in localStorage).
    """
    __tablename__ = "farmer_profile"

    id          = db.Column(db.Integer, primary_key=True)
    session_id  = db.Column(db.String(64), unique=True, nullable=False, index=True)
    state       = db.Column(db.String(60), nullable=True)
    district    = db.Column(db.String(80), nullable=True)
    language    = db.Column(db.String(20), default="english")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    queries     = db.relationship("QueryHistory", backref="farmer", lazy=True,
                                   cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "state":      self.state,
            "district":   self.district,
            "language":   self.language,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QueryHistory(db.Model):
    """
    Stores each query a farmer makes, so we can show them "last time you asked about X".
    """
    __tablename__ = "query_history"

    id          = db.Column(db.Integer, primary_key=True)
    session_id  = db.Column(db.String(64), db.ForeignKey("farmer_profile.session_id"), nullable=False)
    category    = db.Column(db.String(30), nullable=False)   # advice, soil, weather, market, pesticide, yield
    state       = db.Column(db.String(60), nullable=True)
    district    = db.Column(db.String(80), nullable=True)
    top_crop    = db.Column(db.String(60), nullable=True)     # top recommended crop (if category=advice)
    queried_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "category":   self.category,
            "state":      self.state,
            "district":   self.district,
            "top_crop":   self.top_crop,
            "queried_at": self.queried_at.isoformat(),
        }
