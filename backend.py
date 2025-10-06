from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
import shap
from model import retrain
from model_test import explain_sample_json

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

with open("exoplanet_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("exoplanet_explainer.pkl", "rb") as f:
    explainer = pickle.load(f)

df = pd.read_csv("koi_dataset.csv", comment="#")
features = [
    'koi_depth', 'koi_duration', 'koi_period', 'koi_impact', 'koi_model_snr',
    'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec',
    'koi_prad', 'koi_teq', 'koi_insol', 'koi_steff', 'koi_srad', 'koi_slogg'
]
X = df[features].fillna(0)

@app.route("/api/explain_sample", methods=["GET"])
def api_explain_sample():
    idx = int(request.args.get("index", 0))
    json_data = explain_sample_json(idx)
    return json_data, 200, {'Content-Type': 'application/json'}

@app.route("/api/retrain", methods=["POST"])
def api_retrain():
    try:
        feedback = request.json
        retrain(feedback)
        return jsonify({"status": "success", "message": "Model updated with scientist feedback."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Backend is running"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
