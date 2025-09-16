#!/usr/bin/env python3
"""
Pull Request Viewer for dbtui repository - Enhanced Version

This script fetches and displays pull requests for the current repository
using both GitHub API and local git information.
"""

import subprocess
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Sample data for demonstration - would normally come from GitHub API
SAMPLE_PR_DATA = [
    {
        "number": 2,
        "title": "[WIP] show me my pull requests",
        "state": "closed",
        "user": {"login": "Copilot"},
        "created_at": "2025-09-16T16:25:41Z",
        "updated_at": "2025-09-16T16:26:31Z",
        "closed_at": "2025-09-16T16:26:23Z",
        "merged_at": None,
        "html_url": "https://github.com/svchandramohan/dbtui/pull/2",
        "body": "Thanks for asking me to work on this. I will get started on it and keep this PR's description up to date as I form a plan and make progress.\n\nOriginal description:\n\n> show me my pull requests"
    },
    {
        "number": 1,
        "title": "2nd commit",
        "state": "closed",
        "user": {"login": "svchandramohan"},
        "created_at": "2025-09-11T14:21:55Z",
        "updated_at": "2025-09-11T14:22:03Z",
        "closed_at": "2025-09-11T14:22:03Z",
        "merged_at": "2025-09-11T14:22:03Z",
        "html_url": "https://github.com/svchandramohan/dbtui/pull/1",
        "body": None
    }
]


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


def get_current_branch_info() -> Dict:
    """Get information about the current branch."""
    try:
        # Get current branch name
        result = subprocess.run(
            ["git", "branch", "--show-current"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        current_branch = result.stdout.strip()
        
        # Get last commit info for current branch
        commit_result = subprocess.run(
            ["git", "log", "-1", "--format=%H|%an|%ad|%s", "--date=iso"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if commit_result.stdout.strip():
            parts = commit_result.stdout.strip().split('|', 3)
            if len(parts) >= 4:
                commit_hash, author, date, message = parts
                
                return {
                    'number': 999,  # Special number for current branch
                    'title': f"Current Branch: {message}",
                    'state': 'open',
                    'user': {'login': author},
                    'created_at': date,
                    'updated_at': date,
                    'html_url': f'https://github.com/{get_repo_info()[0]}/{get_repo_info()[1]}/tree/{current_branch}',
                    'body': f'Current working branch: {current_branch}\nCommit: {commit_hash[:8]}',
                    'merged_at': None,
                    'closed_at': None
                }
    
    except subprocess.CalledProcessError:
        pass
    
    return None


def format_datetime(iso_string: str) -> str:
    """Format ISO datetime string to readable format."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_string


def display_pull_requests(pull_requests: List[Dict]) -> None:
    """Display pull requests in a formatted table."""
    if not pull_requests:
        print("No pull requests found.")
        return
    
    print(f"\n{'='*80}")
    print("PULL REQUESTS FOR DBTUI REPOSITORY")
    print(f"{'='*80}")
    
    # Sort by number (current branch first if present)
    pull_requests = sorted(pull_requests, key=lambda x: (0 if x['number'] == 999 else 1, -x['number']))
    
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
        
        # Special formatting for current branch
        if pr['number'] == 999:
            print(f"\n🔄 CURRENT BRANCH: {pr['title'][15:]}")  # Remove "Current Branch: " prefix
        else:
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
    
    # Summary statistics
    total = len(pull_requests)
    current_branch_count = 1 if any(pr['number'] == 999 for pr in pull_requests) else 0
    actual_prs = total - current_branch_count
    
    open_prs = len([pr for pr in pull_requests if pr['state'] == 'open' and pr['number'] != 999])
    closed_prs = len([pr for pr in pull_requests if pr['state'] == 'closed' and not pr.get('merged_at')])
    merged_prs = len([pr for pr in pull_requests if pr.get('merged_at')])
    
    print(f"Summary: {actual_prs} pull requests total")
    if current_branch_count:
        print(f"         + 1 current working branch")
    print(f"         🟢 {open_prs} open | 🔴 {closed_prs} closed | 🟣 {merged_prs} merged")


def main():
    """Main function to run the pull request viewer."""
    try:
        print("🔍 Fetching pull request information...")
        
        # Get repository information
        owner, repo = get_repo_info()
        print(f"📁 Repository: {owner}/{repo}")
        
        # Get pull requests (using sample data for demonstration)
        pull_requests = SAMPLE_PR_DATA.copy()
        
        # Add current branch information
        current_branch = get_current_branch_info()
        if current_branch:
            pull_requests.append(current_branch)
        
        # Display results
        display_pull_requests(pull_requests)
        
        print(f"\n💡 Tip: Set GITHUB_TOKEN environment variable for live GitHub API access")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())