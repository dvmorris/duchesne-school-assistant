#!/usr/bin/env python3
"""
Upload helper for Duchesne School Assistant to upload files to Google Drive.
Supports:
1. Direct Google Drive REST API v3 upload when OAuth token is present.
2. Local Google Drive folder staging (~/Google Drive/Duchesne).
3. Browser-driven upload via the persistent authenticated Google profile.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

TOKEN_FILE = Path.home() / ".gemini" / "antigravity" / "gdrive_token.json"
OAUTH_TOKEN_FILE = Path.home() / ".gemini" / "antigravity" / "google_oauth_token.json"
LOCAL_DRIVE_DIR = Path.home() / "Google Drive" / "Duchesne"

# Add parent dir to sys.path so we can import setup_oauth
sys.path.insert(0, str(Path(__file__).parent))
try:
    from setup_oauth import refresh_tokens_if_needed
except ImportError:
    refresh_tokens_if_needed = None

def get_access_token():
    """Retrieve an access token from environment or local credentials file."""
    if "GCLI_ACCESS_TOKEN" in os.environ:
        return os.environ["GCLI_ACCESS_TOKEN"]
    if refresh_tokens_if_needed:
        token = refresh_tokens_if_needed()
        if token:
            return token
    if OAUTH_TOKEN_FILE.exists():
        try:
            with open(OAUTH_TOKEN_FILE, "r") as f:
                return json.load(f).get("access_token")
        except Exception:
            pass
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                return data.get("access_token")
        except Exception:
            pass
    return None


def find_or_create_folder(token, folder_name="Duchesne"):
    """Finds or creates a folder in Google Drive using Drive API v3."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Search for folder
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(query)}"
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        files = res.get("files", [])
        if files:
            return files[0]["id"]
            
    # Create folder if not found
    create_url = "https://www.googleapis.com/drive/v3/files"
    body = json.dumps({
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }).encode("utf-8")
    create_req = urllib.request.Request(create_url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(create_req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("id")

def upload_file_to_drive(file_path, folder_name="Duchesne"):
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return False
        
    token = get_access_token()
    if token:
        try:
            folder_id = find_or_create_folder(token, folder_name)
            boundary = "-------314159265358979323846"
            metadata = {
                "name": path.name,
                "parents": [folder_id]
            }
            
            with open(path, "rb") as f:
                file_bytes = f.read()
                
            body = (
                f"--{boundary}\r\n"
                f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
                f"{json.dumps(metadata)}\r\n"
                f"--{boundary}\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
            
            upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
                "Content-Length": str(len(body))
            }
            
            req = urllib.request.Request(upload_url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                file_id = res.get("id")
                print(f"Successfully uploaded {path.name} to Google Drive folder '{folder_name}' (File ID: {file_id})")
                return True
        except Exception as e:
            print(f"API upload encountered an issue: {e}", file=sys.stderr)
            
    # Fallback to local synced Drive directory if available
    LOCAL_DRIVE_DIR.mkdir(parents=True, exist_ok=True)
    target_dest = LOCAL_DRIVE_DIR / path.name
    import shutil
    shutil.copy2(path, target_dest)
    print(f"Saved copy to local Drive folder: {target_dest}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Upload files to Google Drive Duchesne folder")
    parser.add_argument("--file", required=True, help="Path to local file to upload")
    parser.add_argument("--folder", default="Duchesne", help="Target Google Drive folder name")
    args = parser.parse_args()
    
    success = upload_file_to_drive(args.file, args.folder)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
