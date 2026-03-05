import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor
from ydata_profiling import ProfileReport
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from scipy.stats import randint, uniform
import os

plt.style.use('seaborn-v0_8-whitegrid')
np.random.seed(42)
try:
    df = pd.read_csv('Data.csv')
    print("✅ Dataset loaded successfully")
    print(f"📊 Dataset shape: {df.shape}\n")
except FileNotFoundError:
    print("❌ Error: 'Data.csv' not found in current directory")
    exit()

# Validate required columns
required_columns = [
    'price', 'area', 'bedrooms', 'bathrooms', 'stories',
    'mainroad', 'guestroom', 'basement', 'hotwaterheating',
    'airconditioning', 'prefarea', 'furnishingstatus'
]
missing_columns = set(required_columns) - set(df.columns)
if missing_columns:
    print(f"❌ Missing required columns: {missing_columns}")
    exit()

# Validate binary columns
binary_cols = [
    'mainroad', 'guestroom', 'basement',
    'hotwaterheating', 'airconditioning', 'prefarea'
]
for col in binary_cols:
    invalid = ~df[col].isin(['yes', 'no'])
    if invalid.any():
        print(f"❌ Invalid values in {col}: {df[col][invalid].unique()}")
        exit()
print("\n🔍 Generating EDA reports...")
df_eda = df.copy()

# Convert to proper categorical types
categorical_cols = ['furnishingstatus'] + binary_cols
for col in categorical_cols:
    df_eda[col] = df_eda[col].astype(str).str.lower().astype('category')

# Generate standard profile report
profile = ProfileReport(
    df_eda,
    title="House Price Analysis",
    explorative=True,
    config_file=None
)
profile.to_file("House_Price_EDA.html")

# Custom categorical analysis
print("📊 Generating enhanced categorical visualizations...")
os.makedirs('eda_plots', exist_ok=True)

html_content = """<html>
<head><title>Enhanced Categorical Analysis</title></head>
<body style="font-family: Arial; padding: 20px;">
<h1>Enhanced Categorical Analysis</h1>
"""

def create_percent_table(series):
    counts = series.value_counts(dropna=False)
    percents = series.value_counts(normalize=True, dropna=False).mul(100).round(1)
    return pd.DataFrame({'Count': counts, 'Percentage (%)': percents})

for col in categorical_cols:
    html_content += f"<div style='margin: 40px 0; border-top: 2px solid #eee; padding: 20px;'>"
    html_content += f"<h2>{col.title()}</h2>"
    
    # Value counts table
    html_content += "<h3>Distribution</h3>"
    html_content += create_percent_table(df_eda[col]).to_html(classes='data-table', border=0)
    
    # Visualization
    plt.figure(figsize=(12, 6))
    
    if df_eda[col].nunique() == 2:  # Binary features
        ax = sns.countplot(x=df_eda[col], order=df_eda[col].value_counts().index)
        plt.title(f"{col.title()} Distribution", fontsize=14)
        plt.xlabel('')
        
        # Add percentages on bars
        total = len(df_eda[col])
        for p in ax.patches:
            percentage = f'{100 * p.get_height()/total:.1f}%'
            ax.annotate(percentage, 
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', 
                        xytext=(0, 5), 
                        textcoords='offset points')
    else:  # Multi-class features
        plot_data = df_eda[col].value_counts().reset_index()
        plot_data.columns = ['Category', 'Count']
        
        ax = sns.barplot(x='Count', y='Category', data=plot_data, palette='Blues_d')
        plt.title(f"{col.title()} Distribution", fontsize=14)
        plt.xlabel('Count')
        plt.ylabel('')
        
        # Add values on bars
        for p in ax.patches:
            width = p.get_width()
            ax.text(width + 5, p.get_y() + p.get_height()/2,
                    f'{int(width)}',
                    ha='left', va='center')

    plt.tight_layout()
    img_path = f'eda_plots/{col}_distribution.png'
    plt.savefig(img_path, bbox_inches='tight', dpi=100)
    plt.close()
    
    html_content += f"<img src='{img_path}' style='max-width: 800px; margin: 20px 0;'>"
    html_content += "</div>"

html_content += """</body>
<style>
.data-table {
    width: auto !important;
    margin: 15px 0;
    border-collapse: collapse;
}
.data-table th, .data-table td {
    padding: 8px 12px;
    border: 1px solid #ddd;
}
.data-table th {
    background-color: #f8f9fa;
}
</style>
</html>"""

with open("Categorical_Analysis.html", "w") as f:
    f.write(html_content)

print("✅ Generated two reports:")
print("- House_Price_EDA.html (Standard ydata Profiling)")
print("- Categorical_Analysis.html (Custom Visualizations)")
# Convert binary features to 0/1
df[binary_cols] = df[binary_cols].replace({'yes': 1, 'no': 0}).astype(int)

numeric_features = ['area', 'bedrooms', 'bathrooms', 'stories']
categorical_cols = ['furnishingstatus']

preprocessor = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ]), numeric_features),
    ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), categorical_cols)
], remainder='passthrough')
X = df.drop('price', axis=1)
y = df['price']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = {
    'LinearRegression': {
        'model': LinearRegression(),
        'params': {}
    },
    'RandomForest': {
        'model': RandomForestRegressor(random_state=42),
        'params': {
            'regressor__n_estimators': randint(100, 500),
            'regressor__max_depth': randint(2, 20),
            'regressor__min_samples_split': randint(2, 20)
        }
    },
    'XGBoost': {
        'model': XGBRegressor(random_state=42),
        'params': {
            'regressor__n_estimators': randint(100, 500),
            'regressor__max_depth': randint(3, 10),
            'regressor__learning_rate': uniform(0.01, 0.3)
        }
    }
}

results = {}
best_model = None
best_error_ratio = float('inf')

for name, config in models.items():
    print(f"\n⚙️ Tuning {name}...")
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', config['model'])
    ])
    
    search = RandomizedSearchCV(
        pipeline,
        config['params'],
        n_iter=20,
        cv=5,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        random_state=42
    )
    search.fit(X_train, y_train)
    
    # Store best estimator and metrics
    best_estimator = search.best_estimator_
    y_train_pred = best_estimator.predict(X_train)
    y_test_pred = best_estimator.predict(X_test)
    
    results[name] = {
        'Best Estimator': best_estimator,
        'Best Params': search.best_params_,
        'Train Metrics': {
            'R²': r2_score(y_train, y_train_pred),
            'MAE': mean_absolute_error(y_train, y_train_pred),
            'RMSE': np.sqrt(mean_squared_error(y_train, y_train_pred)),
            'Error Ratio': np.sum(np.abs(y_train - y_train_pred)) / np.sum(y_train)
        },
        'Test Metrics': {
            'R²': r2_score(y_test, y_test_pred),
            'MAE': mean_absolute_error(y_test, y_test_pred),
            'RMSE': np.sqrt(mean_squared_error(y_test, y_test_pred)),
            'Error Ratio': np.sum(np.abs(y_test - y_test_pred)) / np.sum(y_test)
        }
    }
    
    if results[name]['Test Metrics']['Error Ratio'] < best_error_ratio:
        best_error_ratio = results[name]['Test Metrics']['Error Ratio']
        best_model = best_estimator

# Print results
print("\n📊 Final Model Evaluation Metrics:")
for model, data in results.items():
    print(f"\n=== {model} ===")
    print(f"Best Parameters: {data['Best Params']}")
    print("\nTraining Set:")
    print(f"R²: {data['Train Metrics']['R²']:.3f} | MAE: {data['Train Metrics']['MAE']:,.2f}")
    print(f"RMSE: {data['Train Metrics']['RMSE']:,.2f} | Error Ratio: {data['Train Metrics']['Error Ratio']:.4f}")
    print("\nTest Set:")
    print(f"R²: {data['Test Metrics']['R²']:.3f} | MAE: {data['Test Metrics']['MAE']:,.2f}")
    print(f"RMSE: {data['Test Metrics']['RMSE']:,.2f} | Error Ratio: {data['Test Metrics']['Error Ratio']:.4f}")

# Retrain best model on full data
best_model.fit(X, y)
print(f"\n🎯 Best Model: {type(best_model.named_steps['regressor']).__name__}")
def plot_feature_importance(model):
    """Visualize feature importance using model's built-in preprocessor"""
    try:
        # Get preprocessor from the trained pipeline
        preprocessor = model.named_steps['preprocessor']
        feature_names = preprocessor.get_feature_names_out()
        
        # Get importance values
        regressor = model.named_steps['regressor']
        if hasattr(regressor, 'feature_importances_'):
            importances = regressor.feature_importances_
        elif hasattr(regressor, 'coef_'):
            importances = regressor.coef_
        else:
            print("⚠️ Model doesn't support feature importance analysis")
            return

        # Create plot with clear labels
        indices = np.argsort(importances)[-10:]
        plt.figure(figsize=(10, 6))
        plt.title('Top 10 Feature Importances')
        plt.barh(range(len(indices)), importances[indices], align='center')
        
        # Clean feature names by removing prefixes
        clean_names = [name.split('__')[-1] for name in feature_names[indices]]
        plt.yticks(range(len(indices)), clean_names)
        plt.xlabel('Relative Importance')
        plt.tight_layout()
        plt.savefig('feature_importance.png')
        plt.close()
        print("✅ Feature importance plot generated successfully")
    except Exception as e:
        print(f"⚠️ Error generating feature importance: {str(e)}")

# Update the call
print("\n🔍 Feature Importance Analysis")
plot_feature_importance(best_model)
def check_collinearity(model):
    """Simplified collinearity check without tabulate dependency"""
    try:
        # Process training data
        preprocessor = model.named_steps['preprocessor']
        X_processed = preprocessor.transform(X_train)
        
        # Calculate VIF for numerical features only
        vif_data = pd.DataFrame({
            'Feature': numeric_features,
            'VIF': [variance_inflation_factor(X_processed[:, :len(numeric_features)], i)
                   for i in range(len(numeric_features))]
        })
        
        print("\n📊 Collinearity Analysis (VIF > 5 indicates high collinearity)")
        print(vif_data.to_string(index=False))
        
    except Exception as e:
        print(f"⚠️ Collinearity check failed: {str(e)}")
        print("Note: Install 'tabulate' for better table formatting: pip install tabulate")

# Update the collinearity check call
if 'LinearRegression' in results:
    print("\n🔍 Checking multicollinearity for linear model")
    check_collinearity(results['LinearRegression']['Best Estimator'])
joblib.dump(best_model, 'best_house_price_model.joblib')
print("\n💾 Best model saved as best_house_price_model.joblib")

def validate_input(feature, value):
    """Validate and convert input features"""
    try:
        if feature in numeric_features:
            val = float(value)
            if feature == 'bedrooms' and not 0 <= val <= 10:
                raise ValueError("Bedrooms must be 0-10")
            if feature == 'bathrooms' and val < 0:
                raise ValueError("Bathrooms can't be negative")
            if feature == 'area' and val < 100:
                raise ValueError("Area must be ≥100 sqft")
            return val
        
        if feature in binary_cols:
            clean_val = str(value).lower().strip()
            if clean_val in ['yes', '1']: return 1
            if clean_val in ['no', '0']: return 0
            raise ValueError(f"Must be yes/no or 0/1 for {feature}")
        
        if feature == 'furnishingstatus':
            valid = ['furnished', 'semi-furnished', 'unfurnished']
            if value.lower() not in valid:
                raise ValueError(f"Must be one of {valid}")
            return value
        
        return value
    except ValueError as e:
        raise ValueError(f"Invalid {feature}: {str(e)}")

def predict_price():
    """Safe prediction interface"""
    print("\n🏠 Property Price Prediction Interface")
    feature_values = {}
    
    for feature in X.columns:
        while True:
            try:
                value = input(f"{feature}: ")
                validated = validate_input(feature, value)
                feature_values[feature] = [validated]
                break
            except ValueError as e:
                print(f"❌ Error: {str(e)}")
    
    try:
        model = joblib.load('best_house_price_model.joblib')
        prediction = model.predict(pd.DataFrame(feature_values))[0]
        print(f"\n💵 Predicted Price: ${prediction:,.2f}")
    except Exception as e:
        print(f"❌ Prediction failed: {str(e)}")

# Uncomment to enable interactive predictions
predict_price()

print("\n🚀 Production-Ready Price Prediction System!")
