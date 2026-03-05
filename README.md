# House Price Prediction — Technical Report

## Architecture Overview

| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| ML Frameworks | Scikit-learn, XGBoost |
| Models Trained | LinearRegression, RandomForest, XGBoost |
| Preprocessing | ColumnTransformer, StandardScaler, OneHotEncoder |
| Profiling | ydata-profiling |
| Serialization | Joblib (`.joblib`) |

### Pipeline
```
[Data.csv] → [EDA + ydata Profiling] → [Feature Engineering]
                                             ↓
                              [3-Model Comparison (RandomizedSearchCV)]
                              ├─ LinearRegression
                              ├─ RandomForestRegressor
                              └─ XGBRegressor
                                             ↓
                              [Best Model Selection] → [best_house_price_model.joblib]
                                             ↓
                              [Interactive Price Prediction CLI]
```

## Study Findings

- **Best Model**: Selected automatically via lowest test error ratio across 3 candidates
- **Validation**: 5-fold cross-validation with RandomizedSearchCV (20 iterations)
- **Metrics**: R², MAE, RMSE, Error Ratio tracked for train/test splits
- **Feature Importance**: Auto-generated plot (`feature_importance.png`)
- **Collinearity Check**: VIF analysis for linear model diagnostics
- **Serialized Artifact**: `best_house_price_model.joblib` (479 KB)
- **Deployment Verdict**: ❌ **Not deployable on free tier** — CLI-only prediction interface, XGBoost + ydata-profiling exceed free tier memory

## Local Setup Guide

```bash
# 1. Navigate to project
cd "House Price Prediction"

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install pandas numpy matplotlib seaborn scikit-learn xgboost joblib \
    ydata-profiling statsmodels scipy

# 4. Ensure Data.csv is in the project directory, then run
python code.py

# 5. The script will:
#    - Generate EDA reports (House_Price_EDA.html, Categorical_Analysis.html)
#    - Train and compare 3 models
#    - Save the best model
#    - Launch interactive prediction CLI
```

## 🔑 API Keys
No API keys required.
