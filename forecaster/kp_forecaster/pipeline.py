import pandas as pd
from .preprocessing import load_and_prepare_data, filter_product
from .feature_engineering import add_lag_features, add_rolling_features, add_time_features, add_ramadhan_feature, create_features_for_step
from .models import get_models, get_base_models
from .evaluation import evaluate, evaluate_predictions
from .config import *
from .bma import calculate_bma_weights
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
import numpy as np

def run_pipeline(filepath):
    df = load_and_prepare_data(filepath)
    df = filter_product(df, TARGET_ID)
    df = add_lag_features(df, N_LAGS, N_WEEKS)
    df = add_rolling_features(df, ROLL_WINDOWS)
    df = add_time_features(df)
    df = add_ramadhan_feature(df)

    df = df.dropna()
    X = df.drop(columns=["TOTAL_JUMLAH"])
    y = df["TOTAL_JUMLAH"]

    X_train, X_test = X[:-TEST_SIZE], X[-TEST_SIZE:]
    y_train, y_test = y[:-TEST_SIZE], y[-TEST_SIZE:]

    results = {}
    for name, model in get_models().items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        metrics = evaluate(y_test, preds)
        results[name] = metrics
        print(f"[{name.upper()}] MSE: {metrics['MSE']:.2f} | MAPE: {metrics['MAPE']:.2%}")
    
    return results

def run_bma_pipeline(file_path, target_product_id, future_step=FUTURE_STEPS):
    """
    Runs the full pipeline including BMA weight calculation, evaluation,
    and future forecasting. (LSTM functionality removed)

    Args:
        filepath (str): Path to the data file.
        target_product_id (str/int): The ID of the product to forecast.

    Returns:
        dict: A dictionary containing BMA weights, individual model forecasts (test set),
              the BMA forecast (test set), actual values (test set), evaluation metrics,
              CV scores, and the future forecast series.
              Returns None if the pipeline fails.
    """
    # --- Load Configuration ---
    # Store config in a dictionary for easier passing
    config = {
        'N_LAGS': N_LAGS, 'N_WEEKS': N_WEEKS, 'ROLL_WINDOWS': ROLL_WINDOWS,
        'TEST_SIZE': TEST_SIZE, 'N_SPLITS_BMA': N_SPLITS_BMA,
        'RANDOM_STATE': 42, 'FUTURE_FORECAST_STEP': future_step
    }


    print(f"--- Starting BMA Pipeline for Product {target_product_id} ---")

    # 1. Load and Prepare Data
    try:
        df_raw = load_and_prepare_data(file_path)
        df_filtered = filter_product(df_raw, target_product_id)
        if df_filtered.empty:
            print(f"ERROR: No data found for product {target_product_id}")
            return None
    except Exception as e:
        print(f"ERROR during data loading/filtering: {e}")
        return None

    # 2. Feature Engineering
    try:
        # Keep the df before dropping NAs, might be useful for feature calculation history
        df_featured = add_lag_features(df_filtered, config['N_LAGS'], config['N_WEEKS'])
        df_featured = add_rolling_features(df_featured, config['ROLL_WINDOWS'])
        df_featured = add_time_features(df_featured)
        df_featured = add_ramadhan_feature(df_featured) # Optional

        df_processed = df_featured.dropna() # This df is used for training/testing

        if df_processed.empty:
            print("ERROR: DataFrame is empty after feature engineering and dropping NA.")
            return None

        # Define features (X) and target (y) based on processed data
        # Ensure target is excluded, and any other non-feature columns like PRODUCT_ID
        potential_non_features = ["TOTAL_JUMLAH", "PRODUCT_ID"]
        feature_names = [col for col in df_processed.columns if col not in potential_non_features]

        if not feature_names:
             print("ERROR: No feature columns found after processing.")
             return None

        X = df_processed[feature_names]
        y = df_processed["TOTAL_JUMLAH"]

    except Exception as e:
        print(f"ERROR during feature engineering: {e}")
        return None

    # Check if enough data for split
    if len(X) <= config['TEST_SIZE']:
        print(f"ERROR: Not enough data ({len(X)} samples) for test set size {config['TEST_SIZE']}")
        return None

    # 3. Split Data
    X_train, X_test = X[:-config['TEST_SIZE']], X[-config['TEST_SIZE']:]
    y_train, y_test = y[:-config['TEST_SIZE']], y[-config['TEST_SIZE']:]
    print(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    test_indices = X_test.index # Store index for test set results

    # --- BMA Specific Steps ---

    # 4. Define Base Models
    base_models = get_base_models()

    # 5. Calculate BMA Weights using Cross-Validation on Training Data
    print(f"\n--- Performing {config['N_SPLITS_BMA']}-Fold CV on Training Data for BMA Weights ---")
    kf = KFold(n_splits=config['N_SPLITS_BMA'], shuffle=True, random_state=config['RANDOM_STATE'])
    cv_mse_scores = {}

    for model_name, model in base_models.items():
        print(f"Cross-validating {model_name}...")
        fold_errors = []
        for fold, (train_index, val_index) in enumerate(kf.split(X_train)):
            X_tr, X_val = X_train.iloc[train_index], X_train.iloc[val_index]
            y_tr, y_val = y_train.iloc[train_index], y_train.iloc[val_index]
            try:
                current_model = model # Assumes fit overwrites previous state
                current_model.fit(X_tr, y_tr)
                y_pred_val = current_model.predict(X_val)
                error = mean_squared_error(y_val, y_pred_val)
                fold_errors.append(error)
            except Exception as e:
                print(f"  ERROR during CV Fold {fold+1} for {model_name}: {e}")
        if fold_errors:
            avg_cv_error = np.mean(fold_errors)
            cv_mse_scores[model_name] = max(avg_cv_error, 1e-9)
            print(f"  {model_name} Avg CV MSE: {avg_cv_error:.4f}")
        else:
            print(f"  {model_name} failed all CV folds.")
            cv_mse_scores[model_name] = float('inf')

    bma_weights = calculate_bma_weights(cv_mse_scores)
    if bma_weights is None: return None
    print("\nCalculated BMA Weights:")
    for name, weight in bma_weights.items():
        if weight > 0: print(f"  {name}: {weight:.4f}")

    # --- Final Model Fitting and Prediction on Test Set ---

    # 6. Fit Final Models on Full Training Data
    print("\n--- Fitting Final Models on Full Training Data ---")
    fitted_models = {}
    temp_bma_weights = bma_weights.copy() # Work with a copy for renormalization

    for model_name, model in base_models.items():
        if temp_bma_weights.get(model_name, 0) > 0:
            print(f"Fitting {model_name}...")
            try:
                model.fit(X_train, y_train)
                fitted_models[model_name] = model
            except Exception as e:
                print(f"  ERROR fitting final {model_name}: {e}")
                temp_bma_weights[model_name] = 0 # Set weight to 0 if final fit fails

    # Renormalize weights if any models failed the final fit
    active_weights = {name: w for name, w in temp_bma_weights.items() if name in fitted_models and w > 0}
    if not active_weights:
        print("ERROR: All models for BMA failed to fit.")
        return None
    weight_sum = sum(active_weights.values())
    if weight_sum < 1e-9 :
         print("ERROR: Sum of weights for successfully fitted models is zero.")
         return None
    elif abs(weight_sum - 1.0) > 1e-6 :
        print("Renormalizing weights after final fit failures.")
        final_bma_weights = {name: (w / weight_sum if name in active_weights else 0)
                             for name, w in temp_bma_weights.items()}
        print("Renormalized BMA Weights:")
        for name, weight in final_bma_weights.items():
             if weight > 0: print(f"  {name}: {weight:.4f}")
    else:
        final_bma_weights = active_weights # Use the weights of successfully fitted models

    # 7. Generate Forecasts on Test Data
    print("\n--- Generating Forecasts on Test Data ---")
    individual_forecasts_test = {}
    bma_forecast_test = np.zeros(len(X_test))
    temp_bma_weights_pred = final_bma_weights.copy() # Copy for prediction renormalization

    for name, model in fitted_models.items():
        weight = temp_bma_weights_pred.get(name, 0)
        if weight > 0:
            print(f"Predicting test set with {name} (Weight: {weight:.4f})")
            try:
                forecast = model.predict(X_test)
                forecast[forecast < 0] = 0 # Ensure non-negative
                individual_forecasts_test[name] = forecast
                bma_forecast_test += weight * forecast
            except Exception as e:
                print(f"  ERROR predicting test set with {name}: {e}")
                individual_forecasts_test[name] = np.zeros(len(X_test))
                temp_bma_weights_pred[name] = 0 # Set weight to 0 if prediction fails

    # Renormalize weights AGAIN if predictions failed for some models
    active_weights_pred = {name: w for name, w in temp_bma_weights_pred.items() if w > 0 and name in fitted_models}
    if not active_weights_pred:
         print("ERROR: All models failed during test set prediction.")
         return None
    weight_sum_pred = sum(active_weights_pred.values())
    if weight_sum_pred < 1e-9 :
        print("ERROR: Sum of weights for successfully predicting models is zero.")
        return None
    elif abs(weight_sum_pred - 1.0) > 1e-6:
        print("Renormalizing weights after prediction failures on test set.")
        final_bma_forecast_test = np.zeros(len(X_test))
        final_bma_weights_for_forecast = {}
        for name, forecast in individual_forecasts_test.items():
             if temp_bma_weights_pred.get(name, 0) > 0 :
                 new_weight = temp_bma_weights_pred[name] / weight_sum_pred
                 final_bma_weights_for_forecast[name] = new_weight
                 final_bma_forecast_test += new_weight * forecast
        bma_forecast_test = final_bma_forecast_test
        final_weights = final_bma_weights_for_forecast # These are the weights used for test and future
        print("Final Renormalized BMA Weights used for forecast:")
        for name, weight in final_weights.items(): print(f"  {name}: {weight:.4f}")
    else:
        # If no renormalization needed, the final weights are those that successfully predicted
        final_weights = active_weights_pred

    print(f"\nFinal BMA Forecast on Test Set (first 5): {np.round(bma_forecast_test[:5], 2)}")
    print(f"Actual Values on Test Set (first 5): {y_test.values[:5]}")

    # 8. Evaluate BMA Forecast on Test Set
    print("\n--- Evaluating Final BMA Forecast on Test Set ---")
    bma_metrics_test = evaluate_predictions(y_test, bma_forecast_test)
    print(f"[BMA Test Set] MSE: {bma_metrics_test['MSE']:.2f} | MAPE: {bma_metrics_test['MAPE']:.2%}")

    individual_metrics_test = {}
    for name, forecast in individual_forecasts_test.items():
        if final_weights.get(name,0) > 0 :
             metrics = evaluate_predictions(y_test, forecast)
             individual_metrics_test[name] = metrics
             print(f"  [{name.upper()} Test Set] MSE: {metrics['MSE']:.2f} | MAPE: {metrics['MAPE']:.2%}")


    # --- 9. Forecast Future Values ---
    print(f"\n--- Forecasting {config['FUTURE_FORECAST_STEP']} Steps into the Future ---")

    # Determine the frequency of the data (e.g., 'W-MON', 'D') for date range generation
    # Infer frequency from the training data index if possible
    inferred_freq = pd.infer_freq(df_processed.index)
    if inferred_freq is None:
        # Default or raise error if frequency cannot be determined - IMPORTANT
        print("WARNING: Could not infer data frequency. Assuming weekly ('W-MON'). Adjust if necessary.")
        inferred_freq = 'W-MON' # Or 'D' for daily, 'M' for monthly etc.

    last_date = df_processed.index[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1 if inferred_freq == 'D' else 7), # Adjust step based on freq
                                 periods=config['FUTURE_FORECAST_STEP'], freq=inferred_freq)

    # Initialize the series for recursive forecasting with historical target values
    # Using df_processed ensures alignment with data used for training features
    extended_series = df_processed["TOTAL_JUMLAH"].copy()
    future_predictions = []

    # Use only models and weights that were successful through fitting and test prediction
    active_models_for_future = {k: v for k, v in fitted_models.items() if k in final_weights}

    print(f"Generating future forecast using models: {list(active_models_for_future.keys())}")

    for future_date in future_dates:
        # Create features for the current future step
        feature_df = create_features_for_step(future_date, extended_series, feature_names, config)

        if feature_df is None:
             print(f"ERROR: Failed to create features for {future_date}. Stopping future forecast.")
             # Handle this - maybe return partial results or None
             future_pred_series = pd.Series(future_predictions, index=future_dates[:len(future_predictions)], name='Forecast') # Partial results
             break # Exit the loop

        # --- Perform BMA prediction for the single future step ---
        bma_pred_step = 0
        for model_name, model in active_models_for_future.items():
            weight = final_weights.get(model_name, 0) # Should always be > 0 here
            try:
                # Predict expects a DataFrame
                pred = model.predict(feature_df)[0] # Get single prediction value
                bma_pred_step += weight * max(pred, 0) # Apply weight and ensure non-negative
            except Exception as e:
                 print(f"  ERROR predicting future step with {model_name} for {future_date}: {e}")
                 # How to handle model failure here? Could skip model, renormalize weights for the step, or stop.
                 # For simplicity, we might ignore the failing model's contribution for this step,
                 # but this will slightly skew the BMA result. A more robust solution might be needed.
                 pass # Ignoring contribution for now

        # Store prediction and update the series for the next step's feature calculation
        future_predictions.append(bma_pred_step)
        # Use .loc for safe assignment with timestamp index
        extended_series.loc[future_date] = bma_pred_step

    else: # If the loop completed without break
        # Create final future predictions series
        future_pred_series = pd.Series(future_predictions, index=future_dates, name='Forecast')
        print("\nFuture Forecast (first 5 steps):")
        print(future_pred_series.head())

    # --- 10. Return Results ---
    results = {
        "final_bma_weights": final_weights, # Weights used for test set and future forecast
        "individual_forecasts_test": {name: pd.Series(forecast, index=test_indices)
                                      for name, forecast in individual_forecasts_test.items() if name in final_weights},
        "bma_forecast_test": pd.Series(bma_forecast_test, index=test_indices),
        "actual_values_test": pd.DataFrame({'TANGGAL': df_filtered.index[-config['TEST_SIZE']:], 'TOTAL_JUMLAH': y_test}),
        "predictions_test": pd.DataFrame({'TANGGAL': df_filtered.index[-config['TEST_SIZE']:], 'TOTAL_JUMLAH': bma_forecast_test}),
        "bma_metrics_test": bma_metrics_test,
        "individual_metrics_test": individual_metrics_test,
        "cv_mse_scores": cv_mse_scores,
        "future_forecast": pd.DataFrame({'TANGGAL': future_dates, 'TOTAL_JUMLAH': future_pred_series}),
    }

    print(f"\n--- BMA Pipeline for Product {target_product_id} Finished ---")
    return results