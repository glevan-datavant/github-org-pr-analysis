# GitHub Organization PR Analysis

A tool to analyze how long it takes users to create their first and tenth PRs after joining a GitHub organization.

## Overview

This tool helps GitHub organization administrators and managers understand contributor onboarding patterns by analyzing:

- Time from joining an organization to first PR
- Time from joining to tenth PR
- Statistical analysis of these metrics
- Visualization of trends over time

## Features

- Efficient data collection using GitHub GraphQL API
- Modular architecture for easy maintenance and extension
- Statistical analysis of PR timing patterns
- Visualization of key metrics
- Export to CSV and JSON formats

## Requirements

- Python 3.8+
- GitHub Personal Access Token with appropriate permissions

## Installation

```bash
# Clone the repository
git clone https://github.com/glevan-datavant/github-org-pr-analysis.git
cd github-org-pr-analysis

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Set up your GitHub token
export GITHUB_TOKEN=your_token_here

# Run the analysis
python main.py --org your-organization-name
```

## Output

The tool generates:

1. CSV file with member data
2. JSON file with detailed analysis
3. Visualizations in the output directory
4. Summary report in the console

## License

MIT
