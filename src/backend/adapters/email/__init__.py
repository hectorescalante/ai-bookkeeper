"""Email adapter implementations."""

from backend.adapters.email.outlook_graph_client import OutlookGraphEmailClient
from backend.adapters.email.outlook_oauth import OutlookOAuthManager

__all__ = ["OutlookGraphEmailClient", "OutlookOAuthManager"]
