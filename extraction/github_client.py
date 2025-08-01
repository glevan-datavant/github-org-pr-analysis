import time
import requests
from typing import Dict, Any, Optional
import logging

from config import GITHUB_TOKEN, GITHUB_API_URL, GITHUB_GRAPHQL_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF

logger = logging.getLogger(__name__)

class GitHubClient:
    """Client for interacting with GitHub REST and GraphQL APIs."""
    
    def __init__(self, token: str = GITHUB_TOKEN):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json"
        }
        self.graphql_url = GITHUB_GRAPHQL_URL
        self.rest_url = GITHUB_API_URL
    
    def execute_graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL query with variables."""
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                response = requests.post(
                    self.graphql_url,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "errors" in result:
                        for error in result["errors"]:
                            logger.error(f"GraphQL error: {error}")
                        if "rate limit exceeded" in str(result["errors"]).lower():
                            wait_time = self._get_rate_limit_reset_time()
                            logger.info(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                            time.sleep(wait_time)
                            retries += 1
                            continue
                    return result
                
                if response.status_code == 401:
                    logger.error("Authentication error. Check your GitHub token.")
                    raise Exception("GitHub authentication error")
                
                if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                    wait_time = self._get_rate_limit_reset_time()
                    logger.info(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                
                logger.error(f"GraphQL request failed with status {response.status_code}: {response.text}")
                
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
            
            # Exponential backoff
            wait_time = RETRY_BACKOFF * (2 ** retries)
            logger.info(f"Retrying in {wait_time} seconds... (Attempt {retries+1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            retries += 1
        
        raise Exception(f"Failed to execute GraphQL query after {MAX_RETRIES} retries")
    
    def rest_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a REST API GET request."""
        url = f"{self.rest_url}/{endpoint.lstrip('/')}" 
        retries = 0
        
        while retries <= MAX_RETRIES:
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                
                if response.status_code == 401:
                    logger.error("Authentication error. Check your GitHub token.")
                    raise Exception("GitHub authentication error")
                
                if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                    wait_time = self._get_rate_limit_reset_time()
                    logger.info(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                
                logger.error(f"REST request failed with status {response.status_code}: {response.text}")
                
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
            
            # Exponential backoff
            wait_time = RETRY_BACKOFF * (2 ** retries)
            logger.info(f"Retrying in {wait_time} seconds... (Attempt {retries+1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            retries += 1
        
        raise Exception(f"Failed to execute REST request after {MAX_RETRIES} retries")
    
    def _get_rate_limit_reset_time(self) -> int:
        """Get the time until rate limit reset in seconds."""
        try:
            response = requests.get(
                f"{self.rest_url}/rate_limit",
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                reset_time = data["resources"]["core"]["reset"]
                current_time = int(time.time())
                wait_time = max(reset_time - current_time, 0) + 5  # Add 5 seconds buffer
                return wait_time
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
        
        # Default wait time if we can't get the actual reset time
        return 60