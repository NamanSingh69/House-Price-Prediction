"""
House Price Prediction — Web Inference API
Flask wrapper that loads the pre-trained joblib model and serves predictions.
Training code remains in code.py (local only).
"""
import os
import logging
import joblib
import pandas as pd
from flask import Flask, request, jsonify, render_template_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load pre-trained model at startup
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_house_price_model.joblib')
try:
    model = joblib.load(MODEL_PATH)
    logger.info(f"✅ Model loaded from {MODEL_PATH}")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    model = None

# Feature definitions (from training script)
NUMERIC_FEATURES = ['area', 'bedrooms', 'bathrooms', 'stories', 'parking']
BINARY_FEATURES = ['mainroad', 'guestroom', 'basement', 'hotwaterheating', 'airconditioning', 'prefarea']
CATEGORICAL_FEATURES = ['furnishingstatus']
ALL_FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Price Predictor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0a0f; --surface: #12121a; --surface-2: #1a1a2e;
            --accent: #10b981; --accent-glow: rgba(16,185,129,0.12);
            --text: #e8e8f0; --text-muted: #8888a0;
            --border: rgba(255,255,255,0.06); --radius: 16px;
        }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f url('/static/bg.png') no-repeat center center fixed;
            background-size: cover;
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            margin: 0;
        }
        .container {
            width: 100%;
            max-width: 640px;
            backdrop-filter: blur(12px);
            background: rgba(0, 0, 0, 0.4);
            border-radius: 24px;
            padding: 2.5rem;
            border: 1px solid rgba(16, 185, 129, 0.2);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        h1 {
            font-size: 2rem; font-weight: 700;
            background: linear-gradient(135deg, var(--accent), #34d399);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }
        .subtitle { color: rgba(255,255,255,0.7); font-size: 0.95rem; margin-bottom: 2rem; line-height: 1.5; }
        .card {
            background: rgba(18, 18, 26, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .field label {
            display: block; font-size: 0.75rem; font-weight: 500;
            color: var(--text-muted); text-transform: uppercase;
            letter-spacing: 0.05em; margin-bottom: 0.4rem;
        }
        .field input, .field select {
            width: 100%; padding: 0.75rem; 
            background: rgba(26, 26, 46, 0.4);
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 10px;
            color: var(--text); font-family: inherit; font-size: 0.9rem;
            transition: all 0.2s ease;
        }
        .field input:focus, .field select:focus {
            outline: none; border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        .toggle-row {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem;
            margin-top: 1rem;
        }
        .toggle {
            display: flex; align-items: center; gap: 0.5rem;
            background: rgba(26, 26, 46, 0.4);
            padding: 0.6rem 0.8rem;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px; cursor: pointer; font-size: 0.8rem;
            transition: all 0.2s;
        }
        .toggle:hover {
            border-color: rgba(16, 185, 129, 0.3);
            background: rgba(16, 185, 129, 0.05);
        }
        .toggle input { display: none; }
        .toggle .dot {
            width: 16px; height: 16px; border-radius: 50%;
            border: 2px solid var(--text-muted); transition: all 0.2s;
        }
        .toggle input:checked + .dot {
            background: var(--accent); border-color: var(--accent);
        }
        button {
            width: 100%; padding: 1rem;
            background: linear-gradient(135deg, var(--accent), #059669);
            border: none; border-radius: 12px; color: white;
            font-family: inherit; font-size: 1rem; font-weight: 600;
            cursor: pointer; transition: transform 0.1s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-1px); box-shadow: 0 8px 30px var(--accent-glow); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .result {
            display: none; text-align: center; padding: 2rem;
            background: var(--surface); border: 1px solid var(--accent);
            border-radius: var(--radius);
        }
        .result.show { display: block; }
        .price { font-size: 3rem; font-weight: 700; color: var(--accent); }
        .price-label { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem; }
        .error { color: #ff4d6a; text-align: center; padding: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏠 House Price Predictor</h1>
        <p class="subtitle">ML-powered property valuation using pre-trained XGBoost/RandomForest</p>

        <form id="predict-form">
            <div class="card">
                <div class="grid">
                    <div class="field">
                        <label>Area (sq ft)</label>
                        <input type="number" id="area" value="3000" min="100" required>
                    </div>
                    <div class="field">
                        <label>Bedrooms</label>
                        <input type="number" id="bedrooms" value="3" min="0" max="10" required>
                    </div>
                    <div class="field">
                        <label>Bathrooms</label>
                        <input type="number" id="bathrooms" value="2" min="0" required>
                    </div>
                    <div class="field">
                        <label>Stories</label>
                        <input type="number" id="stories" value="2" min="1" required>
                    </div>
                    <div class="field">
                        <label>Parking Spots</label>
                        <input type="number" id="parking" value="1" min="0" required>
                    </div>
                    <div class="field">
                        <label>Furnishing</label>
                        <select id="furnishingstatus">
                            <option value="unfurnished">Unfurnished</option>
                            <option value="semi-furnished" selected>Semi-Furnished</option>
                            <option value="furnished">Furnished</option>
                        </select>
                    </div>
                </div>
                <div class="toggle-row">
                    <label class="toggle"><input type="checkbox" id="mainroad" checked><span class="dot"></span>Main Road</label>
                    <label class="toggle"><input type="checkbox" id="guestroom"><span class="dot"></span>Guest Room</label>
                    <label class="toggle"><input type="checkbox" id="basement"><span class="dot"></span>Basement</label>
                    <label class="toggle"><input type="checkbox" id="hotwaterheating"><span class="dot"></span>Hot Water</label>
                    <label class="toggle"><input type="checkbox" id="airconditioning" checked><span class="dot"></span>AC</label>
                    <label class="toggle"><input type="checkbox" id="prefarea"><span class="dot"></span>Preferred Area</label>
                </div>
            </div>
            <button type="submit">💰 Predict Price</button>
        </form>

        <div class="result" id="result" style="margin-top:1.5rem;">
            <div class="price" id="price-value">—</div>
            <div class="price-label">Predicted Property Price</div>
        </div>
    </div>

    <script>
        document.getElementById('predict-form').addEventListener('submit', async e => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            btn.disabled = true;
            try {
                const data = {
                    area: +document.getElementById('area').value,
                    bedrooms: +document.getElementById('bedrooms').value,
                    bathrooms: +document.getElementById('bathrooms').value,
                    stories: +document.getElementById('stories').value,
                    parking: +document.getElementById('parking').value,
                    mainroad: document.getElementById('mainroad').checked ? 'yes' : 'no',
                    guestroom: document.getElementById('guestroom').checked ? 'yes' : 'no',
                    basement: document.getElementById('basement').checked ? 'yes' : 'no',
                    hotwaterheating: document.getElementById('hotwaterheating').checked ? 'yes' : 'no',
                    airconditioning: document.getElementById('airconditioning').checked ? 'yes' : 'no',
                    prefarea: document.getElementById('prefarea').checked ? 'yes' : 'no',
                    furnishingstatus: document.getElementById('furnishingstatus').value,
                };
                const res = await fetch('/api/predict', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                if (!res.ok) throw new Error(result.error);
                document.getElementById('price-value').textContent = '$' + result.predicted_price.toLocaleString();
                document.getElementById('result').classList.add('show');
            } catch (err) {
                document.getElementById('price-value').textContent = err.message;
                document.getElementById('result').classList.add('show');
            } finally { btn.disabled = false; }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict house price from input features."""
    if model is None:
        return jsonify({"error": "Model not loaded. Ensure best_house_price_model.joblib exists."}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        # Build feature dataframe matching training format
        features = {
            'area': [float(data.get('area', 3000))],
            'bedrooms': [int(data.get('bedrooms', 3))],
            'bathrooms': [int(data.get('bathrooms', 2))],
            'stories': [int(data.get('stories', 2))],
            'parking': [int(data.get('parking', 1))],
            'mainroad': [data.get('mainroad', 'yes')],
            'guestroom': [data.get('guestroom', 'no')],
            'basement': [data.get('basement', 'no')],
            'hotwaterheating': [data.get('hotwaterheating', 'no')],
            'airconditioning': [data.get('airconditioning', 'yes')],
            'prefarea': [data.get('prefarea', 'no')],
            'furnishingstatus': [data.get('furnishingstatus', 'semi-furnished')],
        }

        df = pd.DataFrame(features)
        prediction = model.predict(df)[0]

        return jsonify({
            "predicted_price": round(float(prediction), 2),
            "input_features": data,
            "model_type": type(model).__name__ if hasattr(model, '__class__') else "Pipeline"
        })

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "ok", "model_loaded": model is not None})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
