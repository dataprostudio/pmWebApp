from flask import Flask, jsonify
import pandas as pd
import ollama

app = Flask(__name__)

def process_event_log():
    df = pd.read_csv("event_log.csv")  # Adjust for JSON if needed
    events = df.to_dict(orient="records")
    
    # Use Llama 3.2 for analysis
    response = ollama.chat("llama3", f"Analyze these events: {events}")
    
    return response["message"]

@app.route("/process-data", methods=["GET"])
def get_process_data():
    data = process_event_log()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
