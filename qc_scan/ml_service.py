from pathlib import Path
import joblib, json, pandas as pd, numpy as np
from django.conf import settings
from collections import Counter

# ====== Load Model & Metadata ======
ARTIFACT_DIR = Path(settings.HU_MODEL_DIR)
rf = joblib.load(ARTIFACT_DIR / "rf_container_code.joblib")
classes = rf.classes_

# Baca urutan fitur dari expected_features.json
with open(ARTIFACT_DIR / "expected_features.json", "r") as f:
    feature_meta = json.load(f)
FEATURE_ORDER = feature_meta.get("feature_order", [])

# ====== Kategori pendukung ======
BUBBLE_CATEGORIES = {"Fragile", "Electronics", "Luxury"}
ALL_CATS = ["Chemical", "Electronics", "Fragile", "Frozen", "Liquid", "Luxury", "Neutral", "Voucher"]

# ====== Feature Builder ======
def _build_features(df_items: pd.DataFrame) -> pd.DataFrame:
    cats = df_items["category"].fillna("Neutral").tolist()
    dist = float(df_items["distance_km"].mean())
    Ls = df_items["item_length_cm"].values
    Ws = df_items["item_width_cm"].values
    Hs = df_items["item_height_cm"].values
    Ws = np.nan_to_num(Ws); Ls = np.nan_to_num(Ls); Hs = np.nan_to_num(Hs)

    # Coba beberapa orientasi box → pilih volume minimum
    options = [(Ls.sum(), Ws.max(), Hs.max()),
               (Ls.max(), Ws.sum(), Hs.max()),
               (Ls.max(), Ws.max(), Hs.sum())]
    # padding ringan (bubble wrap + jarak)
    layers = 2 if any(c in BUBBLE_CATEGORIES for c in cats) and dist > 50 else (1 if any(c in BUBBLE_CATEGORIES for c in cats) else 0)
    pad = layers * 0.3 + 0.5
    options = [(L + 2 * pad, W + 2 * pad, H + 2 * pad) for (L, W, H) in options]
    eff = options[int(np.argmin([L * W * H for (L, W, H) in options]))]

    cnts = Counter(cats)
    feat = {f"cnt_{c.lower()}": cnts.get(c, 0) for c in ALL_CATS}
    feat.update({
        "n_items": len(df_items),
        "distance_km": dist,
        "max_L": float(np.nanmax(Ls)), "max_W": float(np.nanmax(Ws)), "max_H": float(np.nanmax(Hs)),
        "sum_L": float(np.nansum(Ls)), "sum_W": float(np.nansum(Ws)), "sum_H": float(np.nansum(Hs)),
        "sum_vol": float(np.nansum(df_items["item_volume_cm3"].values)),
        "max_weight": float(np.nanmax(df_items["item_weight_g"].values)),
        "sum_weight": float(np.nansum(df_items["item_weight_g"].values)),
        "eff_L": eff[0], "eff_W": eff[1], "eff_H": eff[2],
    })

    # reindex ke urutan sesuai model training
    X = pd.DataFrame([feat])
    for col in FEATURE_ORDER:
        if col not in X.columns:
            X[col] = 0
    X = X.reindex(columns=FEATURE_ORDER, fill_value=0)
    return X

# ====== Rekomendasi Box + Bubble Wrap ======
def recommend_box_with_wrap(df_items: pd.DataFrame) -> dict:
    X = _build_features(df_items)
    proba = rf.predict_proba(X)[0]
    box_code = str(classes[int(np.argmax(proba))])

    mask = df_items["category"].isin(BUBBLE_CATEGORIES)
    cols = [c for c in ["item_id", "category"] if c in df_items.columns]
    wrap_items = df_items.loc[mask, cols].to_dict(orient="records")

    return {
        "container_code": box_code,
        "need_bubble_wrap": bool(wrap_items),
        "bubble_wrap_items": wrap_items,
    }
