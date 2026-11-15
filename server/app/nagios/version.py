"""Checks the latest Nagios Core release published on GitHub and holds the result in
module-level variables.
"""
import requests
from datetime import datetime, timezone
from flask import current_app

latest = ""

last_checked = datetime.now(timezone.utc)

def check_latest_version():
    """Ask the GitHub releases API for the latest Nagios Core release and derive the
    version number from its tag. An HTTP error is logged and swallowed.
    """
    try:
        response = requests.get(
            "https://api.github.com/repos/NagiosEnterprises/nagioscore/releases/latest",
            timeout=10
        )
        response.raise_for_status()
        
        latest = response.json()["tag_name"].split("-")[1]
        
        last_checked = datetime.now(timezone.utc)
    except requests.exceptions.HTTPError as e:
        current_app.logger.exception(f"Error: {e}")
    
    
