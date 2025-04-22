from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

def get_models():
    return {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=50, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, random_state=42),
        "LightGBM": LGBMRegressor(n_estimators=100, random_state=42, verbose=-1),
        "CatBoost": CatBoostRegressor(n_estimators=100, random_state=42, verbose=0),
    }

def get_base_models(): # Removed input_shape parameter
    """Returns a dictionary of base models for BMA."""
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=50, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, random_state=42, objective='reg:squarederror'), # Specify objective
        "LightGBM": LGBMRegressor(n_estimators=100, random_state=42, verbose=-1),
        "CatBoost": CatBoostRegressor(n_estimators=100, random_state=42, verbose=0),
        # Removed LSTM entry
    }
    return models