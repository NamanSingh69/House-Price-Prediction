import os
import logging
import urllib.request
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for the React frontend development
CORS(app)

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
    return jsonify({"status": "ok", "model_status": "ai_fallback_active"})

def do_predict():
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

    # AI Fallback Inference (bypassing 250MB Lambda limits)
    prompt = f"""You are a highly precise algorithmic real estate pricer.
Given these property details:
Area: {validated_data.area} sqft
Bedrooms: {validated_data.bedrooms}
Bathrooms: {validated_data.bathrooms}
Stories: {validated_data.stories}
Parking Spaces: {validated_data.parking}
Main Road: {"yes" if validated_data.mainroad else "no"}
Guestroom: {"yes" if validated_data.guestroom else "no"}
Basement: {"yes" if validated_data.basement else "no"}
Hot Water Heating: {"yes" if validated_data.hotwaterheating else "no"}
Air Conditioning: {"yes" if validated_data.airconditioning else "no"}
Preferred Area: {"yes" if validated_data.prefarea else "no"}
Furnishing: {validated_data.furnishingstatus}

Estimate a realistic price in USD. Output ONLY a raw valid JSON object with a single key 'predicted_price' containing the raw integer number. No markdown, no text. Example: {{"predicted_price": 450000}}"""

    api_key = request.headers.get("X-Gemini-Key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "Gemini API key missing"}), 401

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up potential markdown formatting
            text_response = text_response.replace('```json', '').replace('```', '').strip()
            parsed_json = json.loads(text_response)
            prediction = parsed_json['predicted_price']
            
            logger.info(f"AI Prediction successful: ${prediction:,.2f}")
            return jsonify({'predicted_price': round(float(prediction), 2)})
            
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        logger.error(f"AI Prediction HTTP error: {err_msg}")
        return jsonify({'error': 'Inference failed via AI fallback'}), 500
    except Exception as e:
        logger.error(f"AI Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    return do_predict()

@app.route('/api/analyze', methods=['POST', 'OPTIONS'])
def analyze_market():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    return do_analyze_market()

# Fallback for Vercel's rewrite quirks just in case
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    if 'predict' in request.path or 'predict' in path:
        return do_predict()
    elif 'analyze' in request.path or 'analyze' in path:
        return do_analyze_market()
        
    return jsonify({"error": "Invalid API endpoint", "path": request.path}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
