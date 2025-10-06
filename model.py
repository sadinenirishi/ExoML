import pandas as pd
import numpy as np
import shap
import pickle
import json

data_path = "koi_dataset.csv"
df = pd.read_csv(data_path, comment='#')

features = [
    'koi_depth', 'koi_duration', 'koi_period', 'koi_impact', 'koi_model_snr',
    'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec',
    'koi_prad', 'koi_teq', 'koi_insol', 'koi_steff', 'koi_srad', 'koi_slogg'
]

X = df[features].fillna(0)

with open("exoplanet_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("exoplanet_explainer.pkl", "rb") as f:
    explainer = pickle.load(f)

criteria_map = {
    'Transit Signal Reliability': ['koi_depth', 'koi_duration', 'koi_period', 'koi_model_snr', 'koi_impact'],
    'False Positive Likelihood': ['koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec'],
    'Planetary Plausibility': ['koi_prad', 'koi_depth', 'koi_srad'],
    'Orbit Plausibility': ['koi_period', 'koi_duration', 'koi_impact'],
    'Temperature Plausibility': ['koi_teq', 'koi_insol', 'koi_steff']
}

def compute_criteria_scores(shap_vals, sample_df):
    scores = {}
    for criterion, feat_list in criteria_map.items():
        scores[criterion] = np.mean(np.abs([shap_vals[0][sample_df.columns.get_loc(f)] for f in feat_list]))
    total = sum(scores.values())
    if total == 0:
        return {k: 0 for k in scores.keys()}
    return {k: int(v / total * 100) for k, v in scores.items()}

def explain_sample_json(sample_index):
    sample_features = X.iloc[[sample_index]]
    row = df.iloc[sample_index]
    pred_class = model.predict(sample_features)[0]
    pred_label = row['koi_disposition']
    pred_proba = model.predict_proba(sample_features)[0]
    shap_values = explainer.shap_values(sample_features)
    shap_vals_for_pred = shap_values[pred_class]
    criteria_scores = compute_criteria_scores(shap_vals_for_pred, sample_features)
    visuals = {
        "Transit Signal Reliability": {
            "type": "feature_bars",
            "features_used": {
                "koi_depth": row['koi_depth'],
                "koi_duration": row['koi_duration'],
                "koi_model_snr": row['koi_model_snr'],
                "koi_impact": row['koi_impact'],
                "koi_period": row['koi_period']
            }
        },
        "False Positive Likelihood": {
            "type": "flag_bars",
            "flags": {
                "koi_fpflag_nt": int(row['koi_fpflag_nt']),
                "koi_fpflag_ss": int(row['koi_fpflag_ss']),
                "koi_fpflag_co": int(row['koi_fpflag_co']),
                "koi_fpflag_ec": int(row['koi_fpflag_ec'])
            }
        },
        "Planetary Plausibility": {
            "type": "planet_vs_star",
            "planet_radius": row['koi_prad'],
            "star_radius": row['koi_srad'],
            "ratio": row['koi_prad'] / row['koi_srad'] if row['koi_srad'] > 0 else None
        },
        "Orbit Plausibility": {
            "type": "orbit_plot",
            "period": row['koi_period'],
            "duration": row['koi_duration'],
            "impact": row['koi_impact']
        },
        "Temperature Plausibility": {
            "type": "temperature_gauge",
            "planet_teq": row['koi_teq'],
            "stellar_teff": row['koi_steff'],
            "insolation": row['koi_insol']
        }
    }
    response = {
        "prediction": pred_label,
        "confidence": float(pred_proba[pred_class]),
        "criteria": {}
    }
    for crit, score in criteria_scores.items():
        response["criteria"][crit] = {"score": score, "visual": visuals[crit]}
    return json.dumps(response, indent=2)

print(explain_sample_json(8))
