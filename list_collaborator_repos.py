#!/usr/bin/env python3
"""
Script to list GitHub repositories where you are a collaborator.

This script uses the GitHub API to fetch and display all repositories
where the authenticated user is a collaborator.

Requirements:
    - requests library: pip install requests
    - GitHub Personal Access Token

Usage:
    python list_collaborator_repos.py

Set your GitHub token as an environment variable:
    export GITHUB_TOKEN=your_token_here

Or pass it directly when running:
    GITHUB_TOKEN=your_token python list_collaborator_repos.py
"""

import os
import sys
import json
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found.")
    print("Install it with: pip install requests")
    sys.exit(1)


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variable."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("\nTo set your token:")
        print("  export GITHUB_TOKEN=your_token_here")
        print("\nTo create a token:")
        print("  1. Go to https://github.com/settings/tokens")
        print("  2. Click 'Generate new token' -> 'Generate new token (classic)'")
        print("  3. Give it a name and select 'repo' scope")
        print("  4. Click 'Generate token' and copy the token")
        return None
    return token


def fetch_user_repos(token: str, affiliation: str = 'collaborator') -> List[Dict]:
    """
    Fetch repositories for the authenticated user with specific affiliation.
    
    Args:
        token: GitHub personal access token
        affiliation: Type of affiliation (owner, collaborator, organization_member)
    
    Returns:
        List of repository dictionaries
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    page = 1
    per_page = 100
    
    print(f"Fetching repositories (affiliation: {affiliation})...\n")
    
    while True:
        url = f'https://api.github.com/user/repos'
        params = {
            'affiliation': affiliation,
            'per_page': per_page,
            'page': page,
            'sort': 'updated'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            return repos
        
        page_repos = response.json()
        
        if not page_repos:
            break
            
        repos.extend(page_repos)
        page += 1
        
        # Check if we've reached the last page
        if len(page_repos) < per_page:
            break
    
    return repos


def display_repos(repos: List[Dict], affiliation: str):
    """Display repository information in a formatted way."""
    if not repos:
        print(f"No repositories found where you are a {affiliation}.")
        return
    
    print(f"{'='*80}")
    print(f"Found {len(repos)} repository(ies) where you are a {affiliation}")
    print(f"{'='*80}\n")
    
    for i, repo in enumerate(repos, 1):
        owner = repo['owner']['login']
        name = repo['name']
        full_name = repo['full_name']
        private = "🔒 Private" if repo['private'] else "🌐 Public"
        description = repo.get('description', 'No description')
        url = repo['html_url']
        updated = repo['updated_at'].split('T')[0]
        
        print(f"{i}. {full_name}")
        print(f"   {private}")
        print(f"   Description: {description}")
        print(f"   URL: {url}")
        print(f"   Last updated: {updated}")
        
        # Check permissions
        permissions = repo.get('permissions', {})
        perm_str = []
        if permissions.get('admin'):
            perm_str.append('admin')
        if permissions.get('push'):
            perm_str.append('push')
        if permissions.get('pull'):
            perm_str.append('pull')
        
        if perm_str:
            print(f"   Permissions: {', '.join(perm_str)}")
        
        print()


def main():
    """Main function to run the script."""
    print("GitHub Collaborator Repository Finder")
    print("=" * 80)
    print()
    
    # Get token
    token = get_github_token()
    if not token:
        sys.exit(1)
    
    print("Select what you want to see:")
    print("1. Repositories where you are a collaborator (not owner)")
    print("2. All repositories (owned, collaborator, organization)")
    print("3. Only repositories you own")
    print("4. Only organization repositories")
    print()
    
    choice = input("Enter your choice (1-4) [default: 1]: ").strip() or "1"
    
    affiliation_map = {
        '1': 'collaborator',
        '2': 'owner,collaborator,organization_member',
        '3': 'owner',
        '4': 'organization_member'
    }
    
    affiliation = affiliation_map.get(choice, 'collaborator')
    
    # Fetch and display repositories
    repos = fetch_user_repos(token, affiliation)
    display_repos(repos, affiliation)
    
    print(f"{'='*80}")
    print("Tip: You can also use the GitHub CLI to list repos:")
    print("  gh repo list --limit 100")
    print("  gh repo list <username> --limit 100")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
