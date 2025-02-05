# House Price Prediction System

A Python-based machine learning system for predicting house prices using regression models. This project includes exploratory data analysis (EDA), data preprocessing, model training/evaluation, and a production-ready prediction interface.

## Features

- **Data Validation**: Checks for required columns and valid binary values
- **Automated EDA**: Generates HTML reports with ydata Profiling and custom visualizations
- **Preprocessing Pipeline**:
  - Handles missing values
  - Scales numerical features
  - Encodes categorical variables
- **Model Comparison**:
  - Linear Regression
  - Random Forest
  - XGBoost
- **Hyperparameter Tuning**: Uses RandomizedSearchCV for optimal model configuration
- **Production Interface**: Interactive CLI for making predictions with saved model

## Dataset Example

```csv
price,area,bedrooms,bathrooms,stories,mainroad,guestroom,basement,hotwaterheating,airconditioning,parking,prefarea,furnishingstatus
13300000,7420,4,2,3,yes,no,no,no,yes,2,yes,furnished
12250000,8960,4,4,4,yes,no,no,no,yes,3,no,unfurnished
12250000,9960,3,2,2,yes,no,yes,no,no,2,yes,semi-furnished
```

## Requirements

- Python 3.8+
- Required packages:
  ```bash
  pip install pandas numpy matplotlib seaborn scikit-learn xgboost ydata-profiling statsmodels joblib
  ```

## Usage

1. **Prepare your data**  
   Ensure your CSV file (`Data.csv`) matches the required format (see example above).

2. **Run the Jupyter notebook**  
   Execute all cells in `code.ipynb` to:
   - Generate EDA reports (`House_Price_EDA.html`, `Categorical_Analysis.html`)
   - Train and compare models
   - Save the best model (`best_house_price_model.joblib`)
   - Create feature importance visualization (`feature_importance.png`)

3. **Make predictions**  
   After training, the notebook will launch an interactive interface:
   ```
   🏠 Property Price Prediction Interface
   area: 5000
   bedrooms: 3
   bathrooms: 2
   stories: 2
   mainroad: yes
   guestroom: no
   basement: no
   hotwaterheating: no
   airconditioning: yes
   parking: 1
   prefarea: yes
   furnishingstatus: semi-furnished

   💵 Predicted Price: $1,234,567.89
   ```

## Key Outputs

- **EDA Reports**: Comprehensive data analysis with statistics and visualizations
- **Model Metrics**:
  | Model          | Test R² | MAE       | RMSE      |
  |----------------|---------|-----------|-----------|
  | LinearRegression | 0.653   | 970,043   | 1,324,507 |
  | RandomForest     | 0.599   | 1,041,018 | 1,423,643 |
  | XGBoost          | 0.648   | 962,950   | 1,333,240 |
- **Feature Importance**: Identifies most influential predictors (e.g., area, bathrooms)
- **Collinearity Check**: VIF analysis for linear regression assumptions

## Project Structure

```
├── Data.csv                 # Input dataset
├── code.ipynb               # Main Jupyter notebook
├── best_house_price_model.joblib  # Saved model
├── House_Price_EDA.html     # Automated EDA report
├── Categorical_Analysis.html# Custom visualization report
├── eda_plots/               # Directory with distribution charts
└── feature_importance.png   # Top 10 influential features
```

## License

MIT License - free for academic and commercial use. Please attribute if referencing this work.
