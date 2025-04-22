from kp_forecaster.pipeline import run_pipeline, run_bma_pipeline
from kp_forecaster.plot import plot_forecast, plot_test_forecast
import time

if __name__ == "__main__":
    filepath = "data/processed.csv"
    # Optional: Create dummy file if needed for placeholder
    # try: load_and_prepare_data(filepath).to_csv(filepath)
    # except Exception as e: print(f"Could not create dummy file: {e}")
    target_product_id = 'MP000294_KD000016_PL000037_SZ000012'

    pipeline_results = run_bma_pipeline(filepath, target_product_id)

    # Save the results to a CSV file
    if pipeline_results:
        results_df = pipeline_results['future_forecast']
        timestamp = time.time()
        results_df.to_csv(f'output/{timestamp}_future_forecast.csv', index=False)
        print("BMA results saved to future_forecast.csv")
    
    if pipeline_results:
        plot_forecast(results_df, target_product_id)
        plot_test_forecast(pipeline_results['predictions_test'], pipeline_results['actual_values_test'], target_product_id)
    else:
        print("BMA pipeline failed, no plot generated.")

    if pipeline_results:
        print("\n--- Pipeline Results Summary ---")
        print("Final BMA Weights:", pipeline_results['final_bma_weights'])
        print("\nBMA Test Set Metrics:", pipeline_results['bma_metrics_test'])
        if pipeline_results['future_forecast'] is not None:
            print("\nFuture Forecast:")
            print(pipeline_results['future_forecast'])
        else:
            print("\nFuture Forecast generation failed or was incomplete.")