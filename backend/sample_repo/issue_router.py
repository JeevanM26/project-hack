"""
Hacktoberfest Issue & PR Auto-Triage Router.
Has case-sensitivity bug and missing body scan for critical crash triage.
"""
from typing import List, Dict

def assign_issue_labels(title: str, body: str) -> List[str]:
    """Assigns triage labels based on issue content."""
    labels = ["hacktoberfest-accepted"]
    
    # BUG IN BASELINE: Case-sensitive search and doesn't inspect body
    if "security" in title:
        labels.append("priority:critical")
    if "crash" in title:
        labels.append("kind:bug")
        
    return labels

def route_pr_reviewer(changed_files: List[str]) -> str:
    """Routes pull request to the appropriate team maintainers."""
    if not changed_files:
        return "unassigned"
    if any("payment" in f or "auth" in f for f in changed_files):
        return "@fintech-core-team"
    return "@community-maintainers"
