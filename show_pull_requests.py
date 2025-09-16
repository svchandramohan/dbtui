#!/usr/bin/env python3
"""
Pull Request Viewer for dbtui repository

This script fetches and displays pull requests for the current repository.
"""

import requests
import json
import os
import subprocess
from datetime import datetime
from typing import List, Dict, Optional


def get_repo_info() -> tuple[str, str]:
    """Extract repository owner and name from git remote URL."""
    try:
        # Get the remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Parse GitHub URL (supports both SSH and HTTPS)
        if remote_url.startswith("git@github.com:"):
            # SSH format: git@github.com:owner/repo.git
            repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
        elif remote_url.startswith("https://github.com/"):
            # HTTPS format: https://github.com/owner/repo.git
            repo_path = remote_url.replace("https://github.com/", "").replace(".git", "")
        else:
            raise ValueError(f"Unsupported remote URL format: {remote_url}")
        
        owner, repo = repo_path.split("/")
        return owner, repo
    
    except subprocess.CalledProcessError:
        raise Exception("Failed to get git remote URL. Make sure you're in a git repository.")
    except ValueError as e:
        raise Exception(f"Failed to parse repository information: {e}")


def fetch_pull_requests_from_git() -> List[Dict]:
    """Fetch pull request information using git commands as fallback."""
    try:
        # Get all branches that look like pull request branches
        result = subprocess.run(
            ["git", "branch", "-r"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        branches = []
        for line in result.stdout.strip().split('\n'):
            branch = line.strip()
            if branch and not branch.startswith('origin/HEAD'):
                branches.append(branch)
        
        # Create mock PR data from git information
        mock_prs = []
        for i, branch in enumerate(branches):
            branch_name = branch.replace('origin/', '')
            
            # Get last commit info for this branch
            try:
                commit_result = subprocess.run(
                    ["git", "log", "-1", "--format=%H|%an|%ad|%s", "--date=iso", branch], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                if commit_result.stdout.strip():
                    parts = commit_result.stdout.strip().split('|', 3)
                    if len(parts) >= 4:
                        commit_hash, author, date, message = parts
                        
                        mock_prs.append({
                            'number': i + 1,
                            'title': message,
                            'state': 'open' if branch_name != 'main' else 'merged',
                            'user': {'login': author},
                            'created_at': date,
                            'updated_at': date,
                            'html_url': f'https://github.com/{get_repo_info()[0]}/{get_repo_info()[1]}/tree/{branch_name}',
                            'body': f'Branch: {branch_name}',
                            'merged_at': date if branch_name == 'main' else None,
                            'closed_at': None
                        })
            except subprocess.CalledProcessError:
                continue
        
        return mock_prs
    
    except subprocess.CalledProcessError:
        return []


def fetch_pull_requests(owner: str, repo: str, state: str = "all") -> List[Dict]:
    """Fetch pull requests from GitHub API with fallback to git commands."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {
        "state": state,
        "sort": "updated", 
        "direction": "desc"
    }
    
    # Check if GitHub token is available for higher rate limits
    github_token = os.environ.get("GITHUB_TOKEN")
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Warning: GitHub API request failed ({e})")
        print("Falling back to local git information...")
        return fetch_pull_requests_from_git()


def format_datetime(iso_string: str) -> str:
    """Format ISO datetime string to readable format."""
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M")


def display_pull_requests(pull_requests: List[Dict]) -> None:
    """Display pull requests in a formatted table."""
    if not pull_requests:
        print("No pull requests found.")
        return
    
    print(f"\n{'='*80}")
    print("PULL REQUESTS")
    print(f"{'='*80}")
    
    for pr in pull_requests:
        status_emoji = {
            "open": "🟢",
            "closed": "🔴",
            "merged": "🟣"
        }
        
        # Determine if PR was merged
        state = pr["state"]
        if state == "closed" and pr.get("merged_at"):
            state = "merged"
        
        print(f"\n#{pr['number']} {status_emoji.get(state, '⚪')} {pr['title']}")
        print(f"   State: {state.upper()}")
        print(f"   Author: {pr['user']['login']}")
        print(f"   Created: {format_datetime(pr['created_at'])}")
        print(f"   Updated: {format_datetime(pr['updated_at'])}")
        
        if pr.get('merged_at'):
            print(f"   Merged: {format_datetime(pr['merged_at'])}")
        elif pr.get('closed_at'):
            print(f"   Closed: {format_datetime(pr['closed_at'])}")
        
        print(f"   URL: {pr['html_url']}")
        
        # Show description if available
        if pr.get('body'):
            body = pr['body'].strip()
            if body:
                # Limit description to first 150 characters
                description = body[:150] + "..." if len(body) > 150 else body
                print(f"   Description: {description}")
    
    print(f"\n{'='*80}")
    print(f"Total: {len(pull_requests)} pull requests")


def main():
    """Main function to run the pull request viewer."""
    try:
        print("Fetching pull request information...")
        
        # Get repository information
        owner, repo = get_repo_info()
        print(f"Repository: {owner}/{repo}")
        
        # Fetch pull requests
        pull_requests = fetch_pull_requests(owner, repo)
        
        # Display results
        display_pull_requests(pull_requests)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())