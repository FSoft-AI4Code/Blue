"""
GitHub integration for Blue CLI - fetch issues, PRs, and repository data.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from termcolor import colored


class GitHubIntegration:
    """Integration with GitHub for fetching issues, PRs, and repository data."""
    
    def __init__(self, token: str, username: Optional[str] = None):
        self.token = token
        self.username = username
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Blue-CLI/1.0'
        })
        
        # Cache
        self.cache: Dict[str, Any] = {}
        self.last_fetch: Optional[datetime] = None
    
    async def test_connection(self) -> bool:
        """Test connection to GitHub API."""
        try:
            response = self.session.get(f"{self.base_url}/user", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(colored(f"GitHub connection test failed: {e}", "red"))
            return False
    
    async def fetch_repository_info(self, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch repository information."""
        try:
            response = self.session.get(f"{self.base_url}/repos/{repo}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data['name'],
                    'full_name': data['full_name'],
                    'description': data.get('description', ''),
                    'language': data.get('language', 'Unknown'),
                    'stars': data['stargazers_count'],
                    'forks': data['forks_count'],
                    'issues': data['open_issues_count'],
                    'default_branch': data['default_branch'],
                    'created': data['created_at'],
                    'updated': data['updated_at'],
                    'url': data['html_url']
                }
            else:
                print(colored(f"Failed to fetch repository {repo}: HTTP {response.status_code}", "yellow"))
                return None
                
        except Exception as e:
            print(colored(f"Error fetching GitHub repository {repo}: {e}", "red"))
            return None
    
    async def fetch_issues(self, repo: str, state: str = "open", limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch issues from a repository."""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{repo}/issues",
                params={
                    'state': state,
                    'per_page': limit,
                    'sort': 'updated',
                    'direction': 'desc'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                issues_data = response.json()
                issues = []
                
                for issue in issues_data:
                    # Skip pull requests (they appear in issues API)
                    if 'pull_request' in issue:
                        continue
                    
                    issues.append({
                        'number': issue['number'],
                        'title': issue['title'],
                        'body': issue.get('body', '')[:200] + '...' if issue.get('body', '') else '',
                        'state': issue['state'],
                        'author': issue['user']['login'],
                        'assignee': issue['assignee']['login'] if issue['assignee'] else None,
                        'labels': [label['name'] for label in issue.get('labels', [])],
                        'created': issue['created_at'],
                        'updated': issue['updated_at'],
                        'url': issue['html_url']
                    })
                
                return issues
            else:
                print(colored(f"Failed to fetch issues: HTTP {response.status_code}", "yellow"))
                return []
                
        except Exception as e:
            print(colored(f"Error fetching GitHub issues: {e}", "red"))
            return []
    
    async def fetch_pull_requests(self, repo: str, state: str = "open", limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch pull requests from a repository."""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{repo}/pulls",
                params={
                    'state': state,
                    'per_page': limit,
                    'sort': 'updated',
                    'direction': 'desc'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                prs_data = response.json()
                prs = []
                
                for pr in prs_data:
                    prs.append({
                        'number': pr['number'],
                        'title': pr['title'],
                        'body': pr.get('body', '')[:200] + '...' if pr.get('body', '') else '',
                        'state': pr['state'],
                        'author': pr['user']['login'],
                        'assignee': pr['assignee']['login'] if pr['assignee'] else None,
                        'base_branch': pr['base']['ref'],
                        'head_branch': pr['head']['ref'],
                        'mergeable': pr.get('mergeable'),
                        'created': pr['created_at'],
                        'updated': pr['updated_at'],
                        'url': pr['html_url']
                    })
                
                return prs
            else:
                print(colored(f"Failed to fetch PRs: HTTP {response.status_code}", "yellow"))
                return []
                
        except Exception as e:
            print(colored(f"Error fetching GitHub PRs: {e}", "red"))
            return []
    
    async def fetch_recent_commits(self, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent commits from a repository."""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{repo}/commits",
                params={
                    'per_page': limit
                },
                timeout=15
            )
            
            if response.status_code == 200:
                commits_data = response.json()
                commits = []
                
                for commit in commits_data:
                    commits.append({
                        'sha': commit['sha'][:8],
                        'message': commit['commit']['message'].split('\n')[0],  # First line only
                        'author': commit['commit']['author']['name'],
                        'date': commit['commit']['author']['date'],
                        'url': commit['html_url']
                    })
                
                return commits
            else:
                return []
                
        except Exception as e:
            print(colored(f"Error fetching GitHub commits: {e}", "red"))
            return []
    
    async def search_issues(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search issues across repositories."""
        try:
            response = self.session.get(
                f"{self.base_url}/search/issues",
                params={
                    'q': query,
                    'per_page': limit,
                    'sort': 'updated'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = []
                
                for issue in data.get('items', []):
                    issues.append({
                        'number': issue['number'],
                        'title': issue['title'],
                        'repository': issue['repository_url'].split('/')[-1],
                        'state': issue['state'],
                        'author': issue['user']['login'],
                        'url': issue['html_url']
                    })
                
                return issues
            else:
                return []
                
        except Exception as e:
            print(colored(f"Error searching GitHub issues: {e}", "red"))
            return []
    
    def get_issue_url(self, repo: str, issue_number: int) -> str:
        """Get URL for an issue."""
        return f"https://github.com/{repo}/issues/{issue_number}"
    
    def get_pr_url(self, repo: str, pr_number: int) -> str:
        """Get URL for a pull request."""
        return f"https://github.com/{repo}/pull/{pr_number}"