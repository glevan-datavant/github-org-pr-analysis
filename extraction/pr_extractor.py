from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from extraction.github_client import GitHubClient
from config import MAX_WORKERS

logger = logging.getLogger(__name__)

class PRExtractor:
    """Extract pull request data for organization members."""
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    def get_user_prs(self, org_name: str, username: str, max_prs: int = 10) -> List[Dict[str, Any]]:
        """Get a user's PRs in the organization using GraphQL API."""
        logger.info(f"Fetching PRs for user {username} in organization {org_name}")
        prs = []
        cursor = None
        has_next_page = True
        
        # This query gets PRs and filters by organization in Python
        # We could use the organizations filter, but it's more flexible to filter in code
        query = """
        query ($username: String!, $cursor: String) {
          user(login: $username) {
            pullRequests(
              first: 100,
              orderBy: {field: CREATED_AT, direction: ASC},
              after: $cursor
            ) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                number
                title
                createdAt
                repository {
                  name
                  owner {
                    login
                  }
                }
                url
              }
            }
          }
        }
        """
        
        while has_next_page and len(prs) < max_prs:
            variables = {
                "username": username,
                "cursor": cursor
            }
            
            try:
                result = self.client.execute_graphql(query, variables)
                
                user_data = result.get("data", {}).get("user")
                if not user_data:
                    logger.warning(f"No user data found for {username}")
                    break
                
                pr_data = user_data.get("pullRequests", {})
                page_info = pr_data.get("pageInfo", {})
                
                # Filter PRs to only include those in the organization
                for pr in pr_data.get("nodes", []):
                    if pr["repository"]["owner"]["login"].lower() == org_name.lower():
                        prs.append(pr)
                        if len(prs) >= max_prs:
                            break
                
                has_next_page = page_info.get("hasNextPage", False)
                if has_next_page:
                    cursor = page_info.get("endCursor")
                
            except Exception as e:
                logger.error(f"Error fetching PRs for {username}: {e}")
                break
        
        logger.info(f"Fetched {len(prs)} PRs for {username}")
        return prs
    
    def enrich_members_with_prs(self, org_name: str, members: List[Dict[str, Any]], max_prs_per_user: int = 10) -> List[Dict[str, Any]]:
        """Add PR data to member information using parallel requests."""
        logger.info(f"Enriching {len(members)} members with PR data")
        
        def process_member(member):
            username = member["login"]
            prs = self.get_user_prs(org_name, username, max_prs_per_user)
            
            if prs:
                # Add first PR data
                member["first_pr"] = prs[0]
                member["first_pr_date"] = prs[0]["createdAt"]
                member["first_pr_url"] = prs[0]["url"]
                
                # Add tenth PR data if available
                if len(prs) >= 10:
                    member["tenth_pr"] = prs[9]
                    member["tenth_pr_date"] = prs[9]["createdAt"]
                    member["tenth_pr_url"] = prs[9]["url"]
                
                # Add all PRs for further analysis
                member["prs"] = prs
            
            return member
        
        enriched_members = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_member = {executor.submit(process_member, member): member for member in members}
            for future in as_completed(future_to_member):
                try:
                    enriched_member = future.result()
                    enriched_members.append(enriched_member)
                except Exception as e:
                    member = future_to_member[future]
                    logger.error(f"Error processing PRs for member {member['login']}: {e}")
        
        members_with_prs = [m for m in enriched_members if "first_pr" in m]
        logger.info(f"Successfully enriched {len(members_with_prs)} members with PR data")
        
        return enriched_members