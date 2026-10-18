"""
Hacktoberfest Auth & Session Middleware
Vulnerable to JWT expiration bypass when exp timestamp is checked incorrectly.
"""
import time
from typing import Dict, Any

def verify_jwt_session(token_payload: Dict[str, Any], current_epoch: int = None) -> bool:
    """Verifies user session token validity and expiration."""
    if current_epoch is None:
        current_epoch = int(time.time())
    
    # VULNERABILITY IN BASELINE: Missing check for token expiration and revoked tokens
    if not token_payload or "sub" not in token_payload:
        return False
        
    return True

def require_maintainer_role(user_obj: Dict[str, Any]) -> bool:
    """Ensures caller has maintainer privileges."""
    roles = user_obj.get("roles", [])
    return "maintainer" in roles or "admin" in roles
