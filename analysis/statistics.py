from typing import Dict, Any, List
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class StatisticsCalculator:
    """Calculate statistical metrics from processed data."""
    
    def calculate_statistics(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key statistics from the analysis data."""
        logger.info("Calculating statistics")
        
        stats = {}
        
        # Basic counts
        stats["total_members"] = analysis_data["total_members"]
        stats["members_with_first_pr"] = analysis_data["members_with_first_pr"]
        stats["members_with_tenth_pr"] = analysis_data["members_with_tenth_pr"]
        
        # Percentages
        stats["percent_with_first_pr"] = (
            analysis_data["members_with_first_pr"] / analysis_data["total_members"] * 100
            if analysis_data["total_members"] > 0 else 0
        )
        stats["percent_with_tenth_pr"] = (
            analysis_data["members_with_tenth_pr"] / analysis_data["total_members"] * 100
            if analysis_data["total_members"] > 0 else 0
        )
        
        # Time to first PR stats
        days_to_first_pr = analysis_data["days_to_first_pr"]
        if days_to_first_pr:
            stats["first_pr_mean_days"] = np.mean(days_to_first_pr)
            stats["first_pr_median_days"] = np.median(days_to_first_pr)
            stats["first_pr_min_days"] = np.min(days_to_first_pr)
            stats["first_pr_max_days"] = np.max(days_to_first_pr)
            stats["first_pr_p25_days"] = np.percentile(days_to_first_pr, 25)
            stats["first_pr_p75_days"] = np.percentile(days_to_first_pr, 75)
            stats["first_pr_std_days"] = np.std(days_to_first_pr)
        
        # Time to tenth PR stats
        days_to_tenth_pr = analysis_data["days_to_tenth_pr"]
        if days_to_tenth_pr:
            stats["tenth_pr_mean_days"] = np.mean(days_to_tenth_pr)
            stats["tenth_pr_median_days"] = np.median(days_to_tenth_pr)
            stats["tenth_pr_min_days"] = np.min(days_to_tenth_pr)
            stats["tenth_pr_max_days"] = np.max(days_to_tenth_pr)
            stats["tenth_pr_p25_days"] = np.percentile(days_to_tenth_pr, 25)
            stats["tenth_pr_p75_days"] = np.percentile(days_to_tenth_pr, 75)
            stats["tenth_pr_std_days"] = np.std(days_to_tenth_pr)
        
        return stats
    
    def analyze_by_time_period(self, analysis_data: Dict[str, Any], period_months: int = 6) -> Dict[str, Any]:
        """Analyze data by time periods to identify trends."""
        logger.info(f"Analyzing data by {period_months}-month periods")
        
        members = analysis_data["members"]
        periods = {}
        
        # Group members by join date periods
        for member in members:
            if "joined_at" not in member:
                continue
                
            try:
                joined_date = datetime.fromisoformat(member["joined_at"].replace('Z', '+00:00'))
                period_key = f"{joined_date.year}-{(joined_date.month-1)//period_months*period_months+1:02d}"
                
                if period_key not in periods:
                    periods[period_key] = {
                        "members": [],
                        "with_first_pr": 0,
                        "with_tenth_pr": 0,
                        "days_to_first_pr": [],
                        "days_to_tenth_pr": []
                    }
                
                periods[period_key]["members"].append(member)
                
                if "days_to_first_pr" in member:
                    periods[period_key]["with_first_pr"] += 1
                    periods[period_key]["days_to_first_pr"].append(member["days_to_first_pr"])
                
                if "days_to_tenth_pr" in member:
                    periods[period_key]["with_tenth_pr"] += 1
                    periods[period_key]["days_to_tenth_pr"].append(member["days_to_tenth_pr"])
                    
            except Exception as e:
                logger.error(f"Error processing member for time period analysis: {e}")
        
        # Calculate statistics for each period
        period_stats = {}
        for period_key, period_data in periods.items():
            stats = {
                "total_members": len(period_data["members"]),
                "with_first_pr": period_data["with_first_pr"],
                "with_tenth_pr": period_data["with_tenth_pr"]
            }
            
            # Calculate percentages
            stats["percent_with_first_pr"] = (
                period_data["with_first_pr"] / stats["total_members"] * 100
                if stats["total_members"] > 0 else 0
            )
            stats["percent_with_tenth_pr"] = (
                period_data["with_tenth_pr"] / stats["total_members"] * 100
                if stats["total_members"] > 0 else 0
            )
            
            # Calculate time to first PR stats
            if period_data["days_to_first_pr"]:
                stats["first_pr_mean_days"] = np.mean(period_data["days_to_first_pr"])
                stats["first_pr_median_days"] = np.median(period_data["days_to_first_pr"])
            
            # Calculate time to tenth PR stats
            if period_data["days_to_tenth_pr"]:
                stats["tenth_pr_mean_days"] = np.mean(period_data["days_to_tenth_pr"])
                stats["tenth_pr_median_days"] = np.median(period_data["days_to_tenth_pr"])
            
            period_stats[period_key] = stats
        
        return period_stats