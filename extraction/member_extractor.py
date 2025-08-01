from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from extraction.github_client import GitHubClient
from config import MAX_WORKERS

logger = logging.getLogger(__name__)

class MemberExtractor:
    """Extract organization member data from GitHub."""
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    def get_org_members(self, org_name: str) -> List[Dict[str, Any]]:
        """Get all members of an organization using GraphQL API."""
        logger.info(f"Fetching members for organization: {org_name}")
        members = []
        cursor = None
        has_next_page = True
        
        query = """
        query ($org: String!, $cursor: String) {
          organization(login: $org) {
            membersWithRole(first: 100, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              edges {
                node {
                  login
                  name
                }
                cursor
              }
            }
          }
        }
        """
        
        while has_next_page:
            variables = {
                "org": org_name,
                "cursor": cursor
            }
            
            result = self.client.execute_graphql(query, variables)
            
            try:
                member_data = result["data"]["organization"]["membersWithRole"]
                page_info = member_data["pageInfo"]
                
                for edge in member_data["edges"]:
                    members.append(edge["node"])
                
                has_next_page = page_info["hasNextPage"]
                if has_next_page:
                    cursor = page_info["endCursor"]
                
                logger.info(f"Fetched {len(members)} members so far")
                
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing member data: {e}")
                logger.debug(f"Response: {result}")
                break
        
        logger.info(f"Total members fetched: {len(members)}")
        return members
    
    def get_membership_date(self, org_name: str, username: str) -> Optional[str]:
        """Get the date when a user joined an organization using REST API."""
        try:
            endpoint = f"orgs/{org_name}/memberships/{username}"
            data = self.client.rest_get(endpoint)
            return data.get("created_at")
        except Exception as e:
            logger.error(f"Error getting membership date for {username}: {e}")
            return None
    
    def enrich_members_with_join_dates(self, org_name: str, members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add join dates to member data using parallel requests."""
        logger.info(f"Enriching {len(members)} members with join dates")
        
        def process_member(member):
            username = member["login"]
            joined_at = self.get_membership_date(org_name, username)
            if joined_at:
                member["joined_at"] = joined_at
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
                    logger.error(f"Error processing member {member['login']}: {e}")
        
        members_with_dates = [m for m in enriched_members if "joined_at" in m]
        logger.info(f"Successfully enriched {len(members_with_dates)} members with join dates")
        
        return enriched_members