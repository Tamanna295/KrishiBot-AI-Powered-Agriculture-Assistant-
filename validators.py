"""
validators.py — Input validation for KrishiBot API
"""

import re
from flask import jsonify

# Allowed language codes
VALID_LANGS = {"english", "hindi", "marathi", "tamil", "telugu", "kannada", "bengali", "gujarati", "punjabi", "odia"}

# Max string lengths
MAX_STATE_LEN   = 60
MAX_DISTRICT_LEN = 80
MAX_CROP_LEN    = 60


def _sanitize_str(value, max_len=100):
    """Strip, limit length, remove dangerous characters."""
    if value is None:
        return ""
    val = str(value).strip()
    # Remove characters that could cause issues (SQL chars, script tags, etc.)
    val = re.sub(r"[<>\"';\\]", "", val)
    return val[:max_len]


def validate_state_district(state, district="", require_district=False):
    """
    Validate state/district params.
    Returns (cleaned_state, cleaned_district, error_response_or_None)
    """
    state    = _sanitize_str(state,    MAX_STATE_LEN)
    district = _sanitize_str(district, MAX_DISTRICT_LEN)

    if not state:
        return "", "", (jsonify({"error": "Missing required parameter: 'state'", "code": "MISSING_STATE"}), 400)

    if len(state) < 2:
        return "", "", (jsonify({"error": "State name is too short", "code": "INVALID_STATE"}), 400)

    if require_district and not district:
        return "", "", (jsonify({"error": "Missing required parameter: 'district'", "code": "MISSING_DISTRICT"}), 400)

    return state, district, None


def validate_lang(lang):
    """Validate language code, default to english."""
    lang = _sanitize_str(lang, 20).lower()
    if lang not in VALID_LANGS:
        lang = "english"
    return lang


def validate_crop(crop):
    """Validate optional crop name."""
    return _sanitize_str(crop, MAX_CROP_LEN)


def validate_npk_ph(n=None, p=None, k=None, ph=None):
    """
    Validate manually-entered NPK and pH values (for direct soil input).
    Returns (dict_of_values, error_or_None)
    """
    result = {}
    try:
        if n is not None:
            n_val = float(n)
            if not (0 <= n_val <= 500):
                return {}, (jsonify({"error": "Nitrogen (N) must be between 0-500 kg/ha", "code": "INVALID_N"}), 400)
            result["N"] = n_val

        if p is not None:
            p_val = float(p)
            if not (0 <= p_val <= 200):
                return {}, (jsonify({"error": "Phosphorus (P) must be between 0-200 kg/ha", "code": "INVALID_P"}), 400)
            result["P"] = p_val

        if k is not None:
            k_val = float(k)
            if not (0 <= k_val <= 200):
                return {}, (jsonify({"error": "Potassium (K) must be between 0-200 kg/ha", "code": "INVALID_K"}), 400)
            result["K"] = k_val

        if ph is not None:
            ph_val = float(ph)
            if not (0 <= ph_val <= 14):
                return {}, (jsonify({"error": "pH must be between 0-14", "code": "INVALID_PH"}), 400)
            result["ph"] = ph_val

    except (ValueError, TypeError):
        return {}, (jsonify({"error": "NPK/pH values must be numbers", "code": "INVALID_NUMERIC"}), 400)

    return result, None
