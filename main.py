from flask import Flask, jsonify, request
from google.cloud import storage

import os
import tensorflow as tf
import tensorflow_text as tf_text

app = Flask(__name__)

BUCKET_NAME = 'kebali-model'
LOCAL_MODEL_BASE_PATH = '/tmp/models'
os.makedirs(LOCAL_MODEL_BASE_PATH, exist_ok=True)

def download_model_from_gcs(bucket_name, model_folder_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=model_folder_name)
    
    model_path = os.path.join(LOCAL_MODEL_BASE_PATH, model_folder_name)
    os.makedirs(model_path, exist_ok=True)
    for blob in blobs:
        if not blob.name.endswith('/'):
            local_file_path = os.path.join(model_path, blob.name[len(model_folder_name) + 1:])
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            blob.download_to_filename(local_file_path)
            print(f"Model file {blob.name} downloaded to {local_file_path}")
    return model_path



@app.route("/", methods=['POST'])
def index():
    data = request.get_json()

    model_code = f"translator-{data['src_lan']}-{data['dst_lan']}"
    model_path = os.path.join(LOCAL_MODEL_BASE_PATH, model_code)
    
    if not os.path.exists(model_path):
        print(f"Downloading model {model_code} from GCS")
        download_model_from_gcs(BUCKET_NAME, model_code)

    model = tf.saved_model.load(model_path)
    
    input_text = data["input_text"]
    result = model.translate([str(input_text)])[0].numpy().decode()
    return jsonify({"result" : str(result).strip()})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
