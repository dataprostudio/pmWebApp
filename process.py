from flask import Flask, jsonify, request
import pandas as pd
import ollama
import json
from datetime import datetime
import numpy as np
import os

app = Flask(__name__)

def create_llama_prompt(events):
    return f"""Analyze this process event log and provide the following in JSON format:
    1. Identify main process steps
    2. Calculate time between steps
    3. Identify potential bottlenecks
    4. List process variants
    
    Event log data:
    {events}
    
    Format response as JSON with these keys:
    {{"process_steps": [], "time_analysis": [], "bottlenecks": [], "variants": []}}
    """

def process_event_log(file_path=None):
    try:
        # Load data from file or use sample data
        if file_path:
            print(f"Attempting to process file: {file_path}")  # Debug log
            file_extension = file_path.split('.')[-1].lower()
            print(f"File extension: {file_extension}")  # Debug log
            
            if file_extension == 'csv':
                try:
                    # First try with comma delimiter
                    df = pd.read_csv(file_path, sep=',', engine='python')
                except:
                    try:
                        # Then try with tab delimiter
                        df = pd.read_csv(file_path, sep='\t', engine='python')
                    except:
                        # Finally try with semicolon delimiter
                        df = pd.read_csv(file_path, sep=';', engine='python')
            elif file_extension == 'txt':
                try:
                    # First try comma-separated
                    df = pd.read_csv(file_path, sep=',', engine='python')
                except:
                    try:
                        # Then try tab-separated
                        df = pd.read_csv(file_path, sep='\t', engine='python')
                    except:
                        # Finally try semicolon-separated
                        df = pd.read_csv(file_path, sep=';', engine='python')
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            print(f"Successfully loaded file with {len(df)} rows")
            print(f"Columns found: {df.columns.tolist()}")
            
        else:
            df = pd.read_csv("event_log.csv")
        
        # Verify required columns exist
        required_columns = ['timestamp', 'event_type', 'user_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean and convert timestamps
        try:
            # First try parsing timestamps as is
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        except:
            try:
                # Try a specific format if automatic parsing fails
                df['timestamp'] = pd.to_datetime(df['timestamp'], 
                                               format='%Y-%m-%d %H:%M:%S', 
                                               errors='coerce')
            except:
                print("Warning: Could not parse some timestamp values")
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        if len(df) == 0:
            raise ValueError("No valid data rows after processing")
            
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Calculate time differences between events
        df['time_diff'] = df.groupby('user_id')['timestamp'].diff()
        
        # Prepare data for Llama analysis
        events_summary = {
            'event_sequence': df.to_dict(orient="records"),
            'avg_time_between_events': df['time_diff'].mean().total_seconds(),
            'total_events': len(df),
            'unique_users': df['user_id'].nunique()
        }
        
        # Get Llama analysis
        prompt = create_llama_prompt(events_summary)
        response = ollama.chat(model="llama3", messages=[
            {
                "role": "user",
                "content": prompt
            }
        ])
        
        # Parse Llama response
        analysis = json.loads(response['message']['content'])
        
        # Enhance analysis with statistical data
        enhanced_analysis = {
            **analysis,
            "statistics": {
                "event_counts": df['event_type'].value_counts().to_dict(),
                "avg_process_duration": df.groupby('user_id')['timestamp'].agg(lambda x: (x.max() - x.min()).total_seconds()).mean(),
                "user_journey_visualization": generate_journey_data(df)
            }
        }
        
        return enhanced_analysis
        
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "file_path": file_path
        }
        print(f"Error processing file: {error_details}")  # Debug log
        return error_details

def generate_journey_data(df):
    """Generate data structure for D3.js visualization"""
    journey_data = {
        "nodes": [],
        "links": []
    }
    
    # Create nodes for each unique event type
    unique_events = df['event_type'].unique()
    for idx, event in enumerate(unique_events):
        journey_data["nodes"].append({
            "id": event,
            "count": int(df[df['event_type'] == event].shape[0])
        })
    
    # Create links between consecutive events
    for user_id in df['user_id'].unique():
        user_events = df[df['user_id'] == user_id]['event_type'].tolist()
        for i in range(len(user_events) - 1):
            link = {
                "source": user_events[i],
                "target": user_events[i + 1],
                "value": 1
            }
            # Check if link exists and update value if it does
            existing_link = next((l for l in journey_data["links"] 
                                if l["source"] == link["source"] and l["target"] == link["target"]), None)
            if existing_link:
                existing_link["value"] += 1
            else:
                journey_data["links"].append(link)
    
    return journey_data

def update_changelog(description):
    """Update the changelog with new entries"""
    changelog_path = 'changelog.md'
    timestamp = datetime.now().isoformat()
    
    entry = f"""
## [{timestamp}]
{description}

"""
    
    try:
        # Create file if it doesn't exist
        if not os.path.exists(changelog_path):
            with open(changelog_path, 'w') as f:
                f.write('# Changelog\n\n')
        
        # Append new entry
        with open(changelog_path, 'a') as f:
            f.write(entry)
        return True
    except Exception as e:
        print(f"Error updating changelog: {str(e)}")
        return False

@app.route("/process-data", methods=["GET", "POST"])
def get_process_data():
    try:
        if request.method == "POST":
            print("POST request received") # Debug log
            
            file = request.files.get('file')
            if file:
                print(f"File received: {file.filename}") # Debug log
                
                file_path = "temp_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + file.filename
                print(f"Saving file to: {file_path}") # Debug log
                
                file.save(file_path)
                print("File saved successfully") # Debug log
                
                data = process_event_log(file_path)
                
                # Clean up temp file
                try:
                    os.remove(file_path)
                except:
                    print(f"Warning: Could not remove temp file: {file_path}")
                
                return jsonify(data)
            else:
                print("No file in request") # Debug log
                return jsonify({"error": "No file provided"})
        
        print("GET request received") # Debug log
        # Default to using event_log.csv if no file uploaded
        data = process_event_log()
        return jsonify(data)
        
    except Exception as e:
        print(f"Error in route handler: {str(e)}") # Debug log
        return jsonify({"error": str(e)})

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(debug=True)
