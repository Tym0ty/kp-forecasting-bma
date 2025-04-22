import pandas as pd
from kp_forecaster.config import PRODUCT_ID_COLS, TARGET_COLUMN, DATE_COLUMN, RESAMPLE_FREQ

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath, parse_dates=[DATE_COLUMN])
    for col in PRODUCT_ID_COLS:
        df[col] = df[col].astype(str)
    df['PRODUCT_ID'] = df[PRODUCT_ID_COLS].agg('_'.join, axis=1)
    return df

def filter_product(df, product_id):
    df = df[df['PRODUCT_ID'] == product_id]
    df = df.groupby(pd.Grouper(key=DATE_COLUMN, freq=RESAMPLE_FREQ))[TARGET_COLUMN].sum().reset_index()
    df = df.rename(columns={TARGET_COLUMN: 'TOTAL_JUMLAH'}).set_index(DATE_COLUMN)
    df = df.asfreq(RESAMPLE_FREQ, fill_value=0)
    return df