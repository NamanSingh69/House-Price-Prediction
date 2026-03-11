import os
import logging
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for the React frontend development
CORS(app)

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

# The Strict Pydantic Zero-Trust Schema
class PredictionRequest(BaseModel):
    area: float
    bedrooms: int
    bathrooms: int
    stories: int
    parking: int
    mainroad: bool
    guestroom: bool
    basement: bool
    hotwaterheating: bool
    airconditioning: bool
    prefarea: bool
    furnishingstatus: str

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model_status": "loaded" if model else "unloaded"})

def do_predict():
    if model is None:
        return jsonify({'error': 'Prediction model is not currently available on the server.'}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
        validated_data = PredictionRequest(**data)
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error: {e.json()}")
        return jsonify({'error': 'Invalid request parameters', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': 'Malformed request'}), 400

    try:
        input_dict = {
            'area': [validated_data.area],
            'bedrooms': [validated_data.bedrooms],
            'bathrooms': [validated_data.bathrooms],
            'stories': [validated_data.stories],
            'parking': [validated_data.parking],
            'mainroad': ['yes' if validated_data.mainroad else 'no'],
            'guestroom': ['yes' if validated_data.guestroom else 'no'],
            'basement': ['yes' if validated_data.basement else 'no'],
            'hotwaterheating': ['yes' if validated_data.hotwaterheating else 'no'],
            'airconditioning': ['yes' if validated_data.airconditioning else 'no'],
            'prefarea': ['yes' if validated_data.prefarea else 'no'],
            'furnishingstatus': [validated_data.furnishingstatus]
        }
        input_df = pd.DataFrame(input_dict)[ALL_FEATURES]
        prediction = model.predict(input_df)[0]
        logger.info(f"Prediction successful: ${prediction:,.2f}")
        return jsonify({'predicted_price': round(float(prediction), 2)})
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

import urllib.request
import json

def do_analyze_market():
    data = request.get_json() or {}
    api_key = request.headers.get("X-Gemini-Key")
    
    if not api_key or not api_key.strip() or api_key == "null":
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY") or "***REDACTED_API_KEY***"
        
    if not api_key:
        return jsonify({"error": "Gemini API key missing"}), 401
        
    gemini_model = data.get("model", "gemini-3.1-pro-preview")
    prompt = data.get("prompt", "")
    
    cascade = [gemini_model] if gemini_model not in ["gemini-3.1-pro-preview", "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash"] else []
    cascade += ["gemini-3.1-pro-preview", "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash"]
    cascade = list(dict.fromkeys(cascade))

    last_err = None
    last_code = 500
    
    for fallback_model in cascade:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{fallback_model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        if "2.5" in fallback_model:
            payload["tools"] = [{"google_search": {}}]
            
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                result['_model_used'] = fallback_model
                return jsonify(result), 200
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode()
            last_err = err_msg
            last_code = e.code
            if e.code in [429, 503] or "exhausted" in err_msg.lower():
                continue
            else:
                break
        except Exception as e:
            last_err = str(e)
            break
            
    return jsonify({"error": last_err}), last_code

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    # Either the path explicitly states the action, or we pass it via query args
    action = request.args.get('action')
    if not action and request.path.endswith('predict'):
        action = 'predict'
    if not action and request.path.endswith('analyze'):
        action = 'analyze'
        
    if action == 'predict':
        return do_predict()
    elif action == 'analyze':
        return do_analyze_market()
        
    return jsonify({"error": "Invalid action or endpoint", "path": request.path}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
