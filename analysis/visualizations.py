from typing import Dict, Any, List
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
from datetime import datetime

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)

class VisualizationGenerator:
    """Generate visualizations from the analyzed data."""
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_time_to_first_pr_histogram(self, days_to_first_pr: List[int], org_name: str):
        """Generate histogram of days to first PR."""
        logger.info("Generating time to first PR histogram")
        
        plt.figure(figsize=(10, 6))
        
        # Create bins with more detail for shorter times
        max_days = min(max(days_to_first_pr), 365)  # Cap at 1 year for better visualization
        
        if max_days <= 30:
            bins = np.arange(0, max_days + 2, 1)  # Daily bins for short timeframes
        elif max_days <= 90:
            bins = np.arange(0, max_days + 7, 7)  # Weekly bins
        else:
            bins = np.arange(0, max_days + 31, 30)  # Monthly bins
        
        plt.hist(days_to_first_pr, bins=bins, alpha=0.7, color='blue', edgecolor='black')
        plt.xlabel('Days from Joining to First PR')
        plt.ylabel('Number of Members')
        plt.title(f'Time to First PR in {org_name}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Add statistics to the plot
        mean_days = np.mean(days_to_first_pr)
        median_days = np.median(days_to_first_pr)
        plt.axvline(mean_days, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_days:.1f} days')
        plt.axvline(median_days, color='green', linestyle='dashed', linewidth=1, label=f'Median: {median_days:.1f} days')
        plt.legend()
        
        file_path = os.path.join(self.output_dir, f"{org_name}_time_to_first_pr_histogram.png")
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved time to first PR histogram to {file_path}")
        return file_path
    
    def generate_time_to_tenth_pr_histogram(self, days_to_tenth_pr: List[int], org_name: str):
        """Generate histogram of days to tenth PR."""
        logger.info("Generating time to tenth PR histogram")
        
        plt.figure(figsize=(10, 6))
        
        # Create appropriate bins
        max_days = min(max(days_to_tenth_pr), 730)  # Cap at 2 years for better visualization
        
        if max_days <= 90:
            bins = np.arange(0, max_days + 7, 7)  # Weekly bins for short timeframes
        elif max_days <= 365:
            bins = np.arange(0, max_days + 31, 30)  # Monthly bins
        else:
            bins = np.arange(0, max_days + 91, 90)  # Quarterly bins
        
        plt.hist(days_to_tenth_pr, bins=bins, alpha=0.7, color='purple', edgecolor='black')
        plt.xlabel('Days from Joining to Tenth PR')
        plt.ylabel('Number of Members')
        plt.title(f'Time to Tenth PR in {org_name}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Add statistics to the plot
        mean_days = np.mean(days_to_tenth_pr)
        median_days = np.median(days_to_tenth_pr)
        plt.axvline(mean_days, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_days:.1f} days')
        plt.axvline(median_days, color='green', linestyle='dashed', linewidth=1, label=f'Median: {median_days:.1f} days')
        plt.legend()
        
        file_path = os.path.join(self.output_dir, f"{org_name}_time_to_tenth_pr_histogram.png")
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved time to tenth PR histogram to {file_path}")
        return file_path
    
    def generate_join_date_vs_first_pr_scatter(self, members: List[Dict[str, Any]], org_name: str):
        """Generate scatter plot of join date vs days to first PR."""
        logger.info("Generating join date vs first PR scatter plot")
        
        # Extract data points
        join_dates = []
        days_to_first_pr = []
        
        for member in members:
            if "joined_at" in member and "days_to_first_pr" in member:
                try:
                    join_date = datetime.fromisoformat(member["joined_at"].replace('Z', '+00:00'))
                    join_dates.append(join_date)
                    days_to_first_pr.append(member["days_to_first_pr"])
                except Exception as e:
                    logger.error(f"Error processing member for scatter plot: {e}")
        
        if not join_dates or not days_to_first_pr:
            logger.warning("No data available for join date vs first PR scatter plot")
            return None
        
        plt.figure(figsize=(12, 6))
        
        # Create scatter plot
        plt.scatter(join_dates, days_to_first_pr, alpha=0.7, s=30)
        
        # Add trend line
        z = np.polyfit([(d - datetime(2000, 1, 1)).total_seconds() for d in join_dates], days_to_first_pr, 1)
        p = np.poly1d(z)
        x_axis = np.array([min(join_dates), max(join_dates)])
        y_axis = p([(d - datetime(2000, 1, 1)).total_seconds() for d in x_axis])
        plt.plot(x_axis, y_axis, "r--", alpha=0.8)
        
        plt.xlabel('Join Date')
        plt.ylabel('Days to First PR')
        plt.title(f'Join Date vs Time to First PR in {org_name}')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        file_path = os.path.join(self.output_dir, f"{org_name}_join_date_vs_first_pr.png")
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved join date vs first PR scatter plot to {file_path}")
        return file_path
    
    def generate_time_period_comparison(self, period_stats: Dict[str, Dict[str, Any]], org_name: str):
        """Generate bar chart comparing statistics across time periods."""
        logger.info("Generating time period comparison chart")
        
        if not period_stats:
            logger.warning("No period data available for time period comparison chart")
            return None
        
        # Sort periods chronologically
        periods = sorted(period_stats.keys())
        
        # Extract data for plotting
        first_pr_medians = []
        tenth_pr_medians = []
        percent_with_first_pr = []
        
        for period in periods:
            stats = period_stats[period]
            if "first_pr_median_days" in stats:
                first_pr_medians.append(stats["first_pr_median_days"])
            else:
                first_pr_medians.append(0)
                
            if "tenth_pr_median_days" in stats:
                tenth_pr_medians.append(stats["tenth_pr_median_days"])
            else:
                tenth_pr_medians.append(0)
                
            percent_with_first_pr.append(stats["percent_with_first_pr"])
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Plot median days to first/tenth PR
        x = np.arange(len(periods))
        width = 0.35
        
        ax1.bar(x - width/2, first_pr_medians, width, label='Median Days to First PR', color='blue', alpha=0.7)
        ax1.bar(x + width/2, tenth_pr_medians, width, label='Median Days to Tenth PR', color='purple', alpha=0.7)
        
        ax1.set_ylabel('Days')
        ax1.set_title(f'Median Time to PRs by Join Period in {org_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Plot percentage with first PR
        ax2.bar(x, percent_with_first_pr, color='green', alpha=0.7)
        ax2.set_ylabel('Percentage (%)')
        ax2.set_xlabel('Join Period')
        ax2.set_title('Percentage of Members with at Least One PR')
        ax2.set_xticks(x)
        ax2.set_xticklabels(periods, rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        file_path = os.path.join(self.output_dir, f"{org_name}_time_period_comparison.png")
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved time period comparison chart to {file_path}")
        return file_path