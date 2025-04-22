def calculate_bma_weights(cv_mse_scores):
    """Calculates BMA weights based on inverse CV MSE."""
    valid_scores = {name: mse for name, mse in cv_mse_scores.items() if mse != float('inf') and mse > 1e-9} # Avoid division by zero or infinity
    if not valid_scores:
        print("\nERROR: No valid CV scores found. Cannot calculate BMA weights.")
        return None

    # Use inverse MSE for weighting
    inverse_error_total = sum(1.0 / mse for mse in valid_scores.values())

    # Handle potential zero total inverse error (if all MSEs were huge)
    if inverse_error_total <= 1e-9:
         print("\nWARNING: Total inverse CV MSE is near zero. Assigning equal weights.")
         num_valid_models = len(valid_scores)
         # Return weights only for models that had valid (non-infinite) scores
         return {name: 1.0 / num_valid_models if name in valid_scores else 0.0 
                 for name in cv_mse_scores.keys()}


    bma_weights = {
        name: (1.0 / mse) / inverse_error_total
        for name, mse in valid_scores.items()
    }

    # Add back models that failed CV with 0 weight
    for name in cv_mse_scores:
        if name not in bma_weights:
            bma_weights[name] = 0.0

    return bma_weights