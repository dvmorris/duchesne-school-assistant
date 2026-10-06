#!/usr/bin/env python3
"""
Google OAuth 2.0 Setup Script for Duchesne School Assistant.
Handles one-time OAuth loopback authorization for:
- Google Photos Library API (https://www.googleapis.com/auth/photoslibrary.appendonly)
- Google Drive API (https://www.googleapis.com/auth/drive.file)
"""

import os
import sys
import json
import time
import argparse
import subprocess
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

TOKEN_STORAGE = Path.home() / ".gemini" / "antigravity" / "google_oauth_token.json"
DEFAULT_PORT = 8085
REDIRECT_URI = f"http://localhost:{DEFAULT_PORT}/"

SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/drive.file"
]

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h2 style="color: #0F9D58;">Authorization Successful!</h2>
                    <p>Duchesne School Assistant has been authorized to upload to Google Photos and Google Drive.</p>
                    <p>You can close this tab and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed: No authorization code returned.")
            
    def log_message(self, format, *args):
        # Suppress standard HTTP server console spam
        pass

def exchange_code_for_tokens(client_id, client_secret, code):
    url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))
        
    tokens["client_id"] = client_id
    tokens["client_secret"] = client_secret
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 3600)
    
    TOKEN_STORAGE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_STORAGE, "w") as f:
        json.dump(tokens, f, indent=2)
    TOKEN_STORAGE.chmod(0o600)
    return tokens

def refresh_tokens_if_needed(tokens=None):
    if tokens is None:
        if not TOKEN_STORAGE.exists():
            return None
        with open(TOKEN_STORAGE, "r") as f:
            tokens = json.load(f)
            
    if time.time() < tokens.get("expires_at", 0) - 120:
        return tokens.get("access_token")
        
    refresh_token = tokens.get("refresh_token")
    client_id = tokens.get("client_id")
    client_secret = tokens.get("client_secret")
    
    if not (refresh_token and client_id and client_secret):
        return None
        
    url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as resp:
            new_tokens = json.loads(resp.read().decode("utf-8"))
            
        tokens["access_token"] = new_tokens.get("access_token")
        tokens["expires_at"] = time.time() + new_tokens.get("expires_in", 3600)
        with open(TOKEN_STORAGE, "w") as f:
            json.dump(tokens, f, indent=2)
        return tokens["access_token"]
    except Exception as e:
        print(f"Error refreshing token: {e}", file=sys.stderr)
        return None

def start_oauth_flow(client_id, client_secret):
    auth_params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    })
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{auth_params}"
    
    server = HTTPServer(("localhost", DEFAULT_PORT), OAuthCallbackHandler)
    server.auth_code = None
    
    print("\n" + "=" * 60)
    print("Opening your browser to authorize Google Photos & Google Drive...")
    print("=" * 60)
    
    # Open in user's default browser or active Chrome
    subprocess.Popen(["open", auth_url])
    
    print(f"Waiting for authorization on {REDIRECT_URI} ...")
    while not server.auth_code:
        server.handle_request()
        
    print("\nReceived authorization code. Exchanging for tokens...")
    tokens = exchange_code_for_tokens(client_id, client_secret, server.auth_code)
    print(f"SUCCESS! OAuth tokens securely saved to: {TOKEN_STORAGE}")
    return tokens

def main():
    parser = argparse.ArgumentParser(description="Google OAuth Setup for Duchesne Assistant")
    parser.add_argument("--client-id", help="Google Cloud OAuth 2.0 Client ID")
    parser.add_argument("--client-secret", help="Google Cloud OAuth 2.0 Client Secret")
    parser.add_argument("--credentials-json", help="Path to downloaded client_secret.json")
    parser.add_argument("--check", action="store_true", help="Check current OAuth token status")
    args = parser.parse_args()
    
    if args.check:
        token = refresh_tokens_if_needed()
        if token:
            print("OAuth status: VALID & ACTIVE")
            print(f"Token storage: {TOKEN_STORAGE}")
            sys.exit(0)
        else:
            print("OAuth status: NOT CONFIGURED OR EXPIRED")
            sys.exit(1)
            
    client_id = args.client_id
    client_secret = args.client_secret
    
    if args.credentials_json and Path(args.credentials_json).exists():
        with open(args.credentials_json, "r") as f:
            data = json.load(f)
            web_or_installed = data.get("installed") or data.get("web") or {}
            client_id = web_or_installed.get("client_id")
            client_secret = web_or_installed.get("client_secret")
            
    if not (client_id and client_secret):
        print("Error: Both --client-id and --client-secret (or --credentials-json) are required.")
        print("\nTo obtain them:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (Application Type: 'Desktop app' or 'Web app')")
        print("3. Ensure Photos Library API and Google Drive API are enabled in your project.")
        print(f"4. Add redirect URI: {REDIRECT_URI}")
        sys.exit(1)
        
    start_oauth_flow(client_id, client_secret)

if __name__ == "__main__":
    main()
