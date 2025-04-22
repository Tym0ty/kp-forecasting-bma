import matplotlib.pyplot as plt
import seaborn as sns

def plot_forecast(df, product_id):
    # Plot Tanggal and Total Jumlah
    # Aggregates df to weekly data

    df = df.resample('W', on='TANGGAL').sum().reset_index()

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=df, x='TANGGAL', y='TOTAL_JUMLAH', label='Total Jumlah', color='blue')
    plt.title(f'Forecast for Product ID: {product_id}')
    plt.xlabel('Tanggal')
    plt.ylabel('Total Jumlah')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    # Save the plot
    plt.savefig(f'output/plot/forecast_plot_{product_id}.png')

def plot_test_forecast(forecast, y, product_id):
    # Plot the forecast vs actual values
    forecast = forecast.resample('W', on='TANGGAL').sum().reset_index()
    y = y.resample('W', on='TANGGAL').sum().reset_index()

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=forecast, x='TANGGAL', y='TOTAL_JUMLAH', label='Forecast', color='blue')
    sns.lineplot(data=y, x='TANGGAL', y='TOTAL_JUMLAH', label='Actual', color='orange')
    plt.title(f'Test Forecast vs Actual for Product ID: {product_id}')
    plt.xlabel('Tanggal')
    plt.ylabel('Total Jumlah')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    # Save the plot
    plt.savefig(f'output/plot/test_forecast_plot_{product_id}.png')