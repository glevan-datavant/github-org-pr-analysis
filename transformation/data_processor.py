from typing import List, Dict, Any
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process raw GitHub API data into a structured format."""
    
    @staticmethod
    def parse_datetime(date_str: str) -> datetime:
        """Parse GitHub API datetime string to datetime object."""
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)
    
    def calculate_time_deltas(self, members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate time deltas between join date and PR dates."""
        logger.info("Calculating time deltas between join dates and PRs")
        
        processed_members = []
        
        for member in members:
            try:
                # Skip members without join date
                if "joined_at" not in member:
                    processed_members.append(member)
                    continue
                
                joined_date = self.parse_datetime(member["joined_at"])
                
                # Calculate time to first PR
                if "first_pr_date" in member:
                    first_pr_date = self.parse_datetime(member["first_pr_date"])
                    delta = first_pr_date - joined_date
                    member["days_to_first_pr"] = delta.days
                    member["hours_to_first_pr"] = delta.total_seconds() / 3600
                
                # Calculate time to tenth PR
                if "tenth_pr_date" in member:
                    tenth_pr_date = self.parse_datetime(member["tenth_pr_date"])
                    delta = tenth_pr_date - joined_date
                    member["days_to_tenth_pr"] = delta.days
                    member["hours_to_tenth_pr"] = delta.total_seconds() / 3600
                
                processed_members.append(member)
                
            except Exception as e:
                logger.error(f"Error calculating time deltas for {member.get('login', 'unknown')}: {e}")
                processed_members.append(member)
        
        return processed_members
    
    def prepare_data_for_analysis(self, members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data structures for analysis."""
        logger.info("Preparing data for analysis")
        
        analysis_data = {
            "total_members": len(members),
            "members_with_join_date": len([m for m in members if "joined_at" in m]),
            "members_with_first_pr": len([m for m in members if "first_pr_date" in m]),
            "members_with_tenth_pr": len([m for m in members if "tenth_pr_date" in m]),
            "days_to_first_pr": [m["days_to_first_pr"] for m in members if "days_to_first_pr" in m],
            "days_to_tenth_pr": [m["days_to_tenth_pr"] for m in members if "days_to_tenth_pr" in m],
            "members": members
        }
        
        return analysis_data