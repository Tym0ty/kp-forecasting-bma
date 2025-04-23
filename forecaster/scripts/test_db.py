import pandas as pd
from datetime import datetime

def add_new_data():
    # Step 1: Load the current data from 'train.csv'
    try:
        df = pd.read_csv('data/train.csv')
    except FileNotFoundError:
        print("train.csv not found. Creating a new file.")
        # If the file doesn't exist, create an empty DataFrame with the required columns
        df = pd.DataFrame(columns=['id', 'CHANNEL', 'LOKASI', 'TANGGAL', 'KODE_BARANG', 
                                   'KLASIFIKASI_BARANG', 'WARNA_BARANG', 'UKURAN_BARANG', 
                                   'BERAT_SATUAN', 'JUMLAH', 'BERAT_TOTAL'])

    # Step 2: Data to be inserted
    new_data = {
        'id': 3,
        'CHANNEL': 1,
        'LOKASI': 'LO000050',
        'TANGGAL': '2024-10-03',
        'KODE_BARANG': 'MP002177',
        'KLASIFIKASI_BARANG': 'KD000039',
        'WARNA_BARANG': 'PL000038',
        'UKURAN_BARANG': 'SZ000014',
        'BERAT_SATUAN': 25.0,
        'JUMLAH': 15,
        'BERAT_TOTAL': 375.0
    }

    # Step 3: Convert the TANGGAL column to datetime for comparison
    df['TANGGAL'] = pd.to_datetime(df['TANGGAL'])

    # Step 4: Define the date range for validation (interval)
    new_data_date = pd.to_datetime(new_data['TANGGAL'])
    start_date = new_data_date - pd.Timedelta(days=2)  # Example: 2 days before the new date
    end_date = new_data_date + pd.Timedelta(days=2)    # Example: 2 days after the new date

    # Step 5: Check if the new date is within the interval range of any existing data
    overlapping_data = df[(df['TANGGAL'] >= start_date) & (df['TANGGAL'] <= end_date)]

    if not overlapping_data.empty:
        print(f"Data for {new_data['TANGGAL']} overlaps with existing data in the interval [{start_date.date()} - {end_date.date()}], skipping insert.")
    else:
        # Step 6: Append the new data to the DataFrame using pd.concat()
        new_row = pd.DataFrame([new_data])  # Convert new data to a DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"New data for {new_data['TANGGAL']} added.")

        # Step 7: Save the updated data back to the CSV
        df.to_csv('data/train.csv', index=False)
        print("Updated data written to 'train.csv'.")

if __name__ == "__main__":
    add_new_data()
