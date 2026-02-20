"""
Meta OAuth Flow for AxGen
Simple Flask app that handles the full OAuth flow:
1. User clicks "Connect Meta Ads"
2. Redirects to Meta login
3. Meta redirects back with auth code
4. We exchange code for access token
5. Store token for API calls
"""

import os
import secrets
import requests
from urllib.parse import urlencode
from flask import Flask, redirect, request, jsonify, render_template_string, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# Meta OAuth Config
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5001/callback")
META_SCOPES = os.getenv("META_SCOPES", "public_profile")
META_CONFIG_ID = os.getenv("META_CONFIG_ID", "")
GRAPH_API_VERSION = "v21.0"

# In-memory token store (use a database in production)
token_store = {}

# ──────────────────────────────────────────────
# HTML Templates
# ──────────────────────────────────────────────

HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>AxGen - Connect Meta Ads</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 80px auto; text-align: center; }
        .btn { display: inline-block; padding: 14px 32px; background: #1877F2; color: white;
               text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold; }
        .btn:hover { background: #166FE5; }
        .status { margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 8px; }
        .connected { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <h1>AxGen</h1>
    <p>Connect your Meta Ads account to get started.</p>
    {% if connected %}
        <div class="status connected">
            <strong>Connected!</strong><br>
            User: {{ user_name }}<br>
            Token stored successfully.
        </div>
        <br>
        <a href="/token">View Token Info</a>
    {% else %}
        <a href="/login" class="btn">Connect Meta Ads</a>
    {% endif %}
</body>
</html>
"""

# ──────────────────────────────────────────────
# Step 1: Home page with "Connect" button
# ──────────────────────────────────────────────

@app.route("/")
def home():
    connected = "user" in token_store
    user_name = token_store.get("user", {}).get("name", "")
    return render_template_string(HOME_PAGE, connected=connected, user_name=user_name)


# ──────────────────────────────────────────────
# Step 2: Redirect user to Meta's OAuth page
# ──────────────────────────────────────────────

@app.route("/login")
def login():
    # Generate CSRF protection token (stored server-side to avoid cookie issues on cross-site redirects)
    state = secrets.token_urlsafe(32)
    token_store['oauth_state'] = state

    oauth_params = {
        "response_type": "code",
        "client_id": META_APP_ID,
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }

    if META_CONFIG_ID:
        oauth_params["config_id"] = META_CONFIG_ID
    else:
        oauth_params["scope"] = META_SCOPES

    params = urlencode(oauth_params)

    meta_oauth_url = f"https://www.facebook.com/dialog/oauth?{params}"
    return redirect(meta_oauth_url)


# ──────────────────────────────────────────────
# Step 3 & 4: Meta redirects here with auth code,
#             we exchange it for an access token
# ──────────────────────────────────────────────

@app.route("/callback")
def callback():
    # Check for errors from Meta
    error = request.args.get("error")
    if error:
        return jsonify({
            "status": "error",
            "error": error,
            "description": request.args.get("error_description", "")
        }), 400

    # Verify state parameter (CSRF protection)
    state = request.args.get("state")
    if state != token_store.get('oauth_state'):
        return jsonify({"status": "error", "message": "Invalid state parameter - possible CSRF attack"}), 401

    # Get the authorization code
    code = request.args.get("code")
    if not code:
        return jsonify({"status": "error", "message": "No authorization code received"}), 400

    # Exchange code for access token
    token_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"
    resp = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "redirect_uri": REDIRECT_URI,
    }, headers={
        "Content-Type": "application/x-www-form-urlencoded",
    })

    if resp.status_code != 200:
        return jsonify({"status": "error", "message": "Token exchange failed", "details": resp.json()}), 400

    token_data = resp.json()
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in")

    # Get user info to confirm it worked
    me = requests.get(f"https://graph.facebook.com/{GRAPH_API_VERSION}/me", params={
        "access_token": access_token,
        "fields": "id,name,email"
    }).json()

    user_name = me.get("name", "Unknown")

    # Store token (in production, save to database)
    token_store["access_token"] = access_token
    token_store["expires_in"] = expires_in
    token_store["user"] = {
        "id": me.get("id"),
        "name": user_name,
        "email": me.get("email"),
    }

    # Print full token to terminal
    print("\n" + "=" * 60)
    print(f"NEW TOKEN - {user_name} ({me.get('email', 'no email')})")
    print("=" * 60)
    print(f"Access Token: {access_token}")
    print(f"Expires in: {expires_in} seconds")
    print("=" * 60 + "\n")

    return redirect("/")


# ──────────────────────────────────────────────
# Utility: View stored token info
# ──────────────────────────────────────────────

@app.route("/token")
def token_info():
    if "access_token" not in token_store:
        return jsonify({"status": "error", "message": "No token stored. Connect first."}), 404

    # Show token preview (first/last 6 chars only)
    token = token_store["access_token"]
    preview = f"{token[:6]}...{token[-6:]}"

    return jsonify({
        "status": "connected",
        "user": token_store.get("user", {}),
        "token_preview": preview,
        "token_length": len(token),
        "expires_in_seconds": token_store.get("expires_in"),
    })


@app.route("/token/full")
def token_full():
    if "access_token" not in token_store:
        return jsonify({"status": "error", "message": "No token stored. Connect first."}), 404
    return jsonify({
        "access_token": token_store["access_token"],
        "user": token_store.get("user", {}),
        "expires_in_seconds": token_store.get("expires_in"),
    })


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if not META_APP_ID or not META_APP_SECRET:
        print("ERROR: Set META_APP_ID and META_APP_SECRET in .env file")
        exit(1)

    print("Starting AxGen Meta OAuth server...")
    print(f"Open http://localhost:5001 in your browser")
    print(f"Callback URL: {REDIRECT_URI}")
    app.run(debug=True, port=5001)
