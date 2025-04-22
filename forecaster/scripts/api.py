# filepath: d:\Code\KP\kp-forecasting-bma\forecaster\scripts\api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from rq import Queue
from redis import Redis
import uuid
from main import run_bma_pipeline

app = Flask(__name__)
CORS(app)

# Connect to Redis
redis_conn = Redis(host='localhost', port=6379)
queue = Queue(connection=redis_conn)

# Store job results in a dictionary (or use Redis for persistence)
job_results = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    target_product_id = request.form.get('target_product_id', 'default_product_id')

    # Save the file temporarily
    filepath = f"temp/{uuid.uuid4()}.csv"
    file.save(filepath)

    # Enqueue the forecasting task
    job_id = str(uuid.uuid4())
    job = queue.enqueue(run_forecasting_task, filepath, target_product_id, job_id)
    return jsonify({"job_id": job_id}), 202

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    if job_id in job_results:
        return jsonify(job_results[job_id])
    return jsonify({"status": "pending"}), 202

def run_forecasting_task(filepath, target_product_id, job_id):
    try:
        # Run the forecasting pipeline
        results = run_bma_pipeline(filepath, target_product_id)
        if results:
            job_results[job_id] = {"status": "completed", "results": results}
        else:
            job_results[job_id] = {"status": "failed", "error": "Pipeline failed"}
    except Exception as e:
        job_results[job_id] = {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    app.run(debug=True)