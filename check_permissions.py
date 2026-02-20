"""
Meta Token Permission Checker
Input an access token → see what permissions/scopes it has.
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")

DEBUG_TOKEN_URL = "https://graph.facebook.com/debug_token"


def get_permissions(access_token):
    """Call Meta's debug_token endpoint to get granted scopes."""
    resp = requests.get(DEBUG_TOKEN_URL, params={
        "input_token": access_token,
        "access_token": f"{META_APP_ID}|{META_APP_SECRET}",
    })

    if resp.status_code != 200:
        print(f"Error: Meta returned status {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    data = resp.json().get("data", {})

    if not data.get("is_valid"):
        print("Token is INACTIVE or EXPIRED.")
        print(f"Full response: {data}")
        return

    print("=" * 50)
    print("TOKEN IS ACTIVE")
    print("=" * 50)

    # Scopes / permissions
    scopes = data.get("scopes", [])

    print(f"\nPermissions ({len(scopes)}):")
    for i, scope in enumerate(scopes, 1):
        print(f"  {i}. {scope}")

    # Extra info
    print(f"\nApp ID:     {data.get('app_id', 'N/A')}")
    print(f"User ID:    {data.get('user_id', 'N/A')}")
    print(f"Type:       {data.get('type', 'N/A')}")
    print(f"Issued at:  {data.get('issued_at', 'N/A')}")
    print(f"Expires at: {data.get('expires_at', 'N/A')}")

    if data.get("granular_scopes"):
        print(f"\nGranular scopes:")
        for gs in data["granular_scopes"]:
            print(f"  - {gs.get('permission', 'N/A')}")

    print()


if __name__ == "__main__":
    if not META_APP_ID or not META_APP_SECRET:
        print("ERROR: Set META_APP_ID and META_APP_SECRET in .env")
        sys.exit(1)

    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = input("Enter Meta access token: ").strip()

    if not token:
        print("No token provided.")
        sys.exit(1)

    get_permissions(token)
