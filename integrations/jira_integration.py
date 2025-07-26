"""
Jira integration for Blue CLI - fetch tickets, issues, and project data.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
from termcolor import colored


class JiraIntegration:
    """Integration with Jira for fetching tickets and project data."""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Cache
        self.cache: Dict[str, Any] = {}
        self.last_fetch: Optional[datetime] = None
    
    async def test_connection(self) -> bool:
        """Test connection to Jira instance."""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/myself", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(colored(f"Jira connection test failed: {e}", "red"))
            return False
    
    async def fetch_ticket(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific ticket by key."""
        try:
            response = self.session.get(
                f"{self.base_url}/rest/api/3/issue/{ticket_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'key': data['key'],
                    'summary': data['fields']['summary'],
                    'description': data['fields'].get('description', {}).get('content', [{}])[0].get('content', [{}])[0].get('text', ''),
                    'status': data['fields']['status']['name'],
                    'assignee': data['fields']['assignee']['displayName'] if data['fields']['assignee'] else None,
                    'priority': data['fields']['priority']['name'] if data['fields']['priority'] else None,
                    'created': data['fields']['created'],
                    'updated': data['fields']['updated'],
                    'url': f"{self.base_url}/browse/{ticket_key}"
                }
            else:
                print(colored(f"Failed to fetch ticket {ticket_key}: HTTP {response.status_code}", "yellow"))
                return None
                
        except Exception as e:
            print(colored(f"Error fetching Jira ticket {ticket_key}: {e}", "red"))
            return None
    
    async def fetch_project_tickets(self, project_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch tickets from a project."""
        try:
            jql = f"project = {project_key} ORDER BY updated DESC"
            
            response = self.session.get(
                f"{self.base_url}/rest/api/3/search",
                params={
                    'jql': jql,
                    'maxResults': limit,
                    'fields': 'summary,status,assignee,priority,created,updated'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                tickets = []
                
                for issue in data.get('issues', []):
                    tickets.append({
                        'key': issue['key'],
                        'summary': issue['fields']['summary'],
                        'status': issue['fields']['status']['name'],
                        'assignee': issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else None,
                        'priority': issue['fields']['priority']['name'] if issue['fields']['priority'] else None,
                        'created': issue['fields']['created'],
                        'updated': issue['fields']['updated'],
                        'url': f"{self.base_url}/browse/{issue['key']}"
                    })
                
                return tickets
            else:
                print(colored(f"Failed to fetch project tickets: HTTP {response.status_code}", "yellow"))
                return []
                
        except Exception as e:
            print(colored(f"Error fetching project tickets: {e}", "red"))
            return []
    
    async def search_tickets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tickets using JQL."""
        try:
            response = self.session.get(
                f"{self.base_url}/rest/api/3/search",
                params={
                    'jql': query,
                    'maxResults': limit,
                    'fields': 'summary,status,assignee,priority,created,updated'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                tickets = []
                
                for issue in data.get('issues', []):
                    tickets.append({
                        'key': issue['key'],
                        'summary': issue['fields']['summary'],
                        'status': issue['fields']['status']['name'],
                        'url': f"{self.base_url}/browse/{issue['key']}"
                    })
                
                return tickets
            else:
                return []
                
        except Exception as e:
            print(colored(f"Error searching Jira tickets: {e}", "red"))
            return []
    
    def get_ticket_url(self, ticket_key: str) -> str:
        """Get URL for a ticket."""
        return f"{self.base_url}/browse/{ticket_key}"