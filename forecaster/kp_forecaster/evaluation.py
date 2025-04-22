from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, mean_absolute_error
import numpy as np

def evaluate(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    return {"MSE": mse, "MAPE": mape}

def evaluate_predictions(y_true, y_pred):
    """Calculates MSE and MAPE."""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    # Handle potential zeros in y_true for MAPE calculation
    mask = y_true != 0
    if np.any(mask):
        mape = mean_absolute_percentage_error(y_true[mask], y_pred[mask])
    else:
        mape = np.inf # Or handle as appropriate if all true values are zero
    return {"MSE": mse, "MAPE": mape, "MAE": mae}