import pandas as pd
ramadhan_dates = {
    2014: ("2014-06-28", "2014-07-27"),
    2015: ("2015-06-18", "2015-07-17"),
    2016: ("2016-06-06", "2016-07-05"),
    2017: ("2017-05-27", "2017-06-25"),
    2018: ("2018-05-16", "2018-06-14"),
    2019: ("2019-05-06", "2019-06-04"),
    2020: ("2020-04-24", "2020-05-23"),
    2021: ("2021-04-13", "2021-05-12"),
    2022: ("2022-04-02", "2022-05-01"),
    2023: ("2023-03-23", "2023-04-21"),
}

eid_dates = {year: pd.to_datetime(date[1]) for year, date in ramadhan_dates.items()}

# Create the is_ramadhan column
def is_ramadhan_day(date):
    year = date.year
    if year in ramadhan_dates:
        start, end = pd.to_datetime(ramadhan_dates[year])
        return int(start <= date <= end)
    return 0

def add_ramadhan_feature(df):
    df['is_ramadhan'] = df.index.to_series().apply(is_ramadhan_day)
    return df

def add_time_features(df):
    df['day'] = df.index.day
    df['month'] = df.index.month
    df['year'] = df.index.year
    df['dayofweek'] = df.index.dayofweek
    df['dayofyear'] = df.index.dayofyear
    df['weekofyear'] = df.index.isocalendar().week
    return df

def add_lag_features(df, n_lags=30, n_weeks=54):
    for i in range(1, n_lags + 1):
        df[f'lag_{i}'] = df['TOTAL_JUMLAH'].shift(i)
    for i in range(1, n_weeks + 1):
        df[f'lag_week_{i}'] = df['TOTAL_JUMLAH'].shift(i * 7)
    return df

def add_rolling_features(df, windows=[7, 30]):
    for window in windows:
        df[f'roll_mean_{window}'] = df['TOTAL_JUMLAH'].shift(1).rolling(window).mean()
    return df

def create_features_for_step(date, extended_series, feature_columns, config):
    """
    Generates the feature set for a single future date step.

    Args:
        date (pd.Timestamp): The future date to create features for.
        extended_series (pd.Series): Series of target values including past predictions, indexed by date.
        feature_columns (list): List of column names the models were trained on.
        config (dict): Dictionary holding configuration like N_LAGS, ROLL_WINDOWS etc.

    Returns:
        pd.DataFrame: A single-row DataFrame with features for the date, or None if error.
    """
    features = {}
    n_lags = config.get('N_LAGS', 4)
    n_weeks = config.get('N_WEEKS', 54) # Should match training
    roll_windows = config.get('ROLL_WINDOWS', [7, 30])

    # --- Calculate features based on extended_series ---

    # Lag features
    # Assumes extended_series is sorted chronologically
    num_historical_points = len(extended_series)
    for lag in range(1, n_lags * n_weeks + 1):
        feature_name = f'lag_{lag}'
        if feature_name in feature_columns: # Only calculate if needed by models
            if num_historical_points >= lag:
                # Get the value 'lag' steps *before* the current prediction point
                features[feature_name] = extended_series.iloc[-lag]
            else:
                # Handle insufficient history (e.g., use mean, median, or 0)
                # Using mean of available history might be reasonable
                features[feature_name] = extended_series.mean() if not extended_series.empty else 0

    # Rolling features (calculated up to the step *before* the current date)
    # Use .iloc[-w:] to get the last 'w' known values *before* the current prediction
    for w in roll_windows:
        feature_name = f'rolling_mean_{w}'
        if feature_name in feature_columns:
            if num_historical_points >= w:
                 # Calculate mean of the last 'w' points in the *current* extended_series
                 features[feature_name] = extended_series.iloc[-w:].mean()
            else:
                # Handle insufficient history
                 features[feature_name] = extended_series.mean() if not extended_series.empty else 0


    # --- Calculate features based on the future date ---
    # Time features (match those created by add_time_features)
    if 'month' in feature_columns: features['month'] = date.month
    if 'week' in feature_columns: features['week'] = date.isocalendar().week
    if 'dayofweek' in feature_columns: features['dayofweek'] = date.dayofweek
    if 'year' in feature_columns: features['year'] = date.year
    if 'dayofyear' in feature_columns: features['dayofyear'] = date.dayofyear
    # Add other time features if they were used in training

    # Ramadhan feature (match logic from add_ramadhan_feature)
    if 'is_ramadhan' in feature_columns:
        features['is_ramadhan'] = is_ramadhan_day(date)

    # --- Create DataFrame and ensure column consistency ---
    try:
        feature_df = pd.DataFrame([features], index=[date])
        # Ensure all columns expected by the model are present and in the correct order
        # Fill missing columns (if any somehow weren't calculated) with 0 or NaN
        # Using 0 here, but consider if NaN and imputation during training requires different handling
        feature_df = feature_df.reindex(columns=feature_columns, fill_value=0)
        return feature_df
    except Exception as e:
        print(f"Error creating feature DataFrame for date {date}: {e}")
        return None