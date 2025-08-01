#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import json
from datetime import datetime

from extraction.github_client import GitHubClient
from extraction.member_extractor import MemberExtractor
from extraction.pr_extractor import PRExtractor
from transformation.data_processor import DataProcessor
from analysis.statistics import StatisticsCalculator
from analysis.visualizations import VisualizationGenerator
from utils.file_handler import FileHandler
from utils.logger import setup_logger
from config import GITHUB_TOKEN, OUTPUT_DIR

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze GitHub organization member PR patterns")
    parser.add_argument("--org", "-o", required=True, help="GitHub organization name")
    parser.add_argument("--token", "-t", help="GitHub personal access token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output", "-d", default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--max-workers", "-w", type=int, default=5, help="Maximum number of concurrent workers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)
    logger = logging.getLogger(__name__)
    
    # Validate GitHub token
    token = args.token or GITHUB_TOKEN
    if not token:
        logger.error("GitHub token not provided. Use --token or set GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize components
    logger.info(f"Initializing analysis for organization: {args.org}")
    github_client = GitHubClient(token)
    member_extractor = MemberExtractor(github_client)
    pr_extractor = PRExtractor(github_client)
    data_processor = DataProcessor()
    stats_calculator = StatisticsCalculator()
    visualizer = VisualizationGenerator(args.output)
    file_handler = FileHandler(args.output)
    
    try:
        # Step 1: Extract organization members
        logger.info("Step 1: Extracting organization members")
        members = member_extractor.get_org_members(args.org)
        
        # Step 2: Enrich members with join dates
        logger.info("Step 2: Enriching members with join dates")
        members = member_extractor.enrich_members_with_join_dates(args.org, members)
        
        # Step 3: Enrich members with PR data
        logger.info("Step 3: Enriching members with PR data")
        members = pr_extractor.enrich_members_with_prs(args.org, members)
        
        # Step 4: Transform data
        logger.info("Step 4: Transforming data")
        members = data_processor.calculate_time_deltas(members)
        analysis_data = data_processor.prepare_data_for_analysis(members)
        
        # Step 5: Calculate statistics
        logger.info("Step 5: Calculating statistics")
        stats = stats_calculator.calculate_statistics(analysis_data)
        period_stats = stats_calculator.analyze_by_time_period(analysis_data)
        
        # Step 6: Generate visualizations
        logger.info("Step 6: Generating visualizations")
        if analysis_data["days_to_first_pr"]:
            visualizer.generate_time_to_first_pr_histogram(analysis_data["days_to_first_pr"], args.org)
        
        if analysis_data["days_to_tenth_pr"]:
            visualizer.generate_time_to_tenth_pr_histogram(analysis_data["days_to_tenth_pr"], args.org)
        
        if analysis_data["members_with_first_pr"] > 0:
            visualizer.generate_join_date_vs_first_pr_scatter(analysis_data["members"], args.org)
            visualizer.generate_time_period_comparison(period_stats, args.org)
        
        # Step 7: Save results
        logger.info("Step 7: Saving results")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save member data to CSV
        csv_file = file_handler.save_to_csv(members, f"{args.org}_members_{timestamp}.csv")
        logger.info(f"Member data saved to {csv_file}")
        
        # Save analysis results to JSON
        results = {
            "organization": args.org,
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "period_statistics": period_stats
        }
        
        json_file = file_handler.save_to_json(results, f"{args.org}_analysis_{timestamp}.json")
        logger.info(f"Analysis results saved to {json_file}")
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"GitHub Organization PR Analysis: {args.org}")
        print("=" * 50)
        print(f"Total members: {stats['total_members']}")
        print(f"Members with at least one PR: {stats['members_with_first_pr']} ({stats['percent_with_first_pr']:.1f}%)")
        print(f"Members with at least ten PRs: {stats['members_with_tenth_pr']} ({stats['percent_with_tenth_pr']:.1f}%)")
        
        if 'first_pr_median_days' in stats:
            print(f"\nTime to first PR:")
            print(f"  Median: {stats['first_pr_median_days']:.1f} days")
            print(f"  Mean: {stats['first_pr_mean_days']:.1f} days")
            print(f"  Range: {stats['first_pr_min_days']:.1f} to {stats['first_pr_max_days']:.1f} days")
        
        if 'tenth_pr_median_days' in stats:
            print(f"\nTime to tenth PR:")
            print(f"  Median: {stats['tenth_pr_median_days']:.1f} days")
            print(f"  Mean: {stats['tenth_pr_mean_days']:.1f} days")
            print(f"  Range: {stats['tenth_pr_min_days']:.1f} to {stats['tenth_pr_max_days']:.1f} days")
        
        print("\nOutput files:")
        print(f"  CSV data: {csv_file}")
        print(f"  JSON analysis: {json_file}")
        print(f"  Visualizations: {args.output}/")
        print("=" * 50)
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
