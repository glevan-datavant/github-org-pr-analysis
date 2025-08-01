import os
import csv
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FileHandler:
    """Handle file operations for saving and loading data."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Save member data to CSV file."""
        if not data:
            logger.warning("No data to save to CSV")
            return ""
        
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            # Determine fields to include
            all_fields = set()
            for item in data:
                all_fields.update(item.keys())
            
            # Remove complex nested fields
            fields_to_exclude = set()
            for field in all_fields:
                for item in data:
                    if field in item and isinstance(item[field], (dict, list)):
                        fields_to_exclude.add(field)
                        break
            
            fields = sorted(list(all_fields - fields_to_exclude))
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                for item in data:
                    writer.writerow(item)
            
            logger.info(f"Saved data to CSV: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving data to CSV: {e}")
            return ""
    
    def save_to_json(self, data: Dict[str, Any], filename: str) -> str:
        """Save analysis results to JSON file."""
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, default=str)
            
            logger.info(f"Saved data to JSON: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")
            return ""
    
    def load_from_json(self, filename: str) -> Dict[str, Any]:
        """Load data from a JSON file."""
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            if not os.path.exists(file_path):
                logger.warning(f"JSON file not found: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            logger.info(f"Loaded data from JSON: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data from JSON: {e}")
            return {}