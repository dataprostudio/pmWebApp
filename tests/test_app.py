import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process import app, process_event_log
from changelog import ChangeLogger

class TestProcessApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    @patch('ollama.chat')
    def test_process_event_log(self, mock_chat):
        # Mock the ollama.chat response
        mock_chat.return_value = {"message": "Test analysis"}
        
        # Test the process_event_log function
        result = process_event_log()
        self.assertEqual(result, "Test analysis")
        
    def test_process_data_endpoint(self):
        # Test the API endpoint
        response = self.app.get('/process-data')
        self.assertEqual(response.status_code, 200)

class TestChangeLogger(unittest.TestCase):
    def setUp(self):
        self.test_log_file = "test_changelog.json"
        self.logger = ChangeLogger(self.test_log_file)
    
    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
    
    def test_log_change(self):
        # Test logging a change
        result = self.logger.log_change(
            "test.py",
            "Test change description",
            "test_author"
        )
        self.assertTrue(result)
        
        # Verify the log file contents
        with open(self.test_log_file, 'r') as f:
            log_data = json.load(f)
        
        self.assertTrue(len(log_data["changes"]) > 0)
        last_change = log_data["changes"][-1]
        self.assertEqual(last_change["file_path"], "test.py")
        self.assertEqual(last_change["description"], "Test change description")
        self.assertEqual(last_change["author"], "test_author")

if __name__ == '__main__':
    unittest.main() 