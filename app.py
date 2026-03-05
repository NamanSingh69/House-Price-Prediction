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

@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Prediction model is not currently available on the server.'}), 503

    try:
        # 1. Zero Trust: Validate incoming JSON using Pydantic
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        # Pydantic validation
        validated_data = PredictionRequest(**data)

    except ValidationError as e:
        logger.error(f"Pydantic Validation Error: {e.json()}")
        return jsonify({'error': 'Invalid request parameters', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': 'Malformed request'}), 400

    try:
        # 2. Reformat data for the pandas ML pipeline
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

        # 3. Create DataFrame honoring explicit feature order
        input_df = pd.DataFrame(input_dict)[ALL_FEATURES]

        # 4. Predict
        prediction = model.predict(input_df)[0]
        
        # Log successful inference
        logger.info(f"Prediction successful: ${prediction:,.2f}")

        # 5. Return JSON payload to the React frontend
        return jsonify({'predicted_price': round(float(prediction), 2)})

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
