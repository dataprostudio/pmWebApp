import os
from datetime import datetime
import json

class ChangeLogger:
    def __init__(self, log_file="changelog.json"):
        self.log_file = log_file
        self._initialize_log()
    
    def _initialize_log(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump({"changes": []}, f, indent=4)
    
    def log_change(self, file_path, change_description, author=None):
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            change_entry = {
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "description": change_description,
                "author": author or os.getenv('USER', 'unknown')
            }
            
            log_data["changes"].append(change_entry)
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error logging change: {str(e)}")
            return False 