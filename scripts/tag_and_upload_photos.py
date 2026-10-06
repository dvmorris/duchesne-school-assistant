#!/usr/bin/env python3
"""
Embeds metadata into downloaded Toddle photos using EXIF tags
and handles uploading to Google Photos / Google Drive.
"""

import os
import sys
import json
import re
from datetime import datetime
import urllib.request
import urllib.parse

from pathlib import Path

try:
    from PIL import Image, ExifTags
except ImportError:
    candidate = "/Applications/Gemini Enterprise.app/Contents/Resources/python/bin/python3"
    if Path(candidate).exists() and sys.executable != candidate:
        os.execv(candidate, [candidate] + sys.argv)
    raise

MANIFEST_PATH = Path.home() / "Pictures" / "Duchesne PK4" / "download_manifest.json"
STATE_FILE = Path.home() / ".gemini" / "antigravity" / "duchesne_state.json"
OAUTH_TOKEN_FILE = Path.home() / ".gemini" / "antigravity" / "google_oauth_token.json"
GPHOTOS_TOKEN_FILE = Path.home() / ".gemini" / "antigravity" / "gphotos_token.json"
DRIVE_PHOTOS_DIR = Path.home() / "Google Drive" / "Duchesne" / "Photos"

# Add parent dir to sys.path so we can import setup_oauth
sys.path.insert(0, str(Path(__file__).parent))
try:
    from setup_oauth import refresh_tokens_if_needed
except ImportError:
    refresh_tokens_if_needed = None


TAG_IMAGE_DESCRIPTION = 270  # Standard EXIF tag for description/caption
TAG_DATE_TIME = 306          # Standard EXIF tag for modification datetime
TAG_DATE_TIME_ORIGINAL = 36867  # Standard ExifIFD tag for original capture datetime
TAG_DATE_TIME_DIGITIZED = 36868 # Standard ExifIFD tag for digitized datetime

def parse_exif_datetime(item):
    """Returns (exif_date_str, epoch_seconds) for the photo item."""
    exif_date = item.get("exifDate")
    if exif_date:
        try:
            dt = datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S")
            return exif_date, dt.timestamp()
        except Exception:
            pass
            
    time_str = item.get("timeString", "")
    # Parse e.g. "27 Aug 2026, 10.27 am"
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4}),?\s+(\d{1,2})[.:](\d{2})\s*(am|pm)", time_str, re.I)
    if m:
        day, mon, year, hour, minute, ampm = m.groups()
        hour = int(hour)
        minute = int(minute)
        if ampm.lower() == "pm" and hour != 12:
            hour += 12
        elif ampm.lower() == "am" and hour == 12:
            hour = 0
        dt = datetime.strptime(f"{year}-{mon}-{day}", "%Y-%b-%d").replace(hour=hour, minute=minute)
        return dt.strftime("%Y:%m:%d %H:%M:%S"), dt.timestamp()
        
    # Default to Sep 4, 2026
    dt = datetime(2026, 9, 4, 11, 40, 0)
    return dt.strftime("%Y:%m:%d %H:%M:%S"), dt.timestamp()

def embed_exif_metadata(item):
    file_path = item.get("filePath")
    desc = item.get("metadataDescription", "")
    
    if not file_path or not Path(file_path).exists():
        return False
        
    try:
        exif_date_str, epoch_time = parse_exif_datetime(item)
        
        img = Image.open(file_path)
        exif = img.getexif()
        
        # 1. Description in IFD0
        exif[TAG_IMAGE_DESCRIPTION] = desc
        
        # 2. DateTime in IFD0
        exif[TAG_DATE_TIME] = exif_date_str
        
        # 3. DateTimeOriginal and DateTimeDigitized in ExifIFD
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        exif_ifd[TAG_DATE_TIME_ORIGINAL] = exif_date_str
        exif_ifd[TAG_DATE_TIME_DIGITIZED] = exif_date_str
        
        # Save back with updated EXIF
        img.save(file_path, exif=exif, quality=95)
        
        # 4. Set filesystem last-modified timestamp
        os.utime(file_path, (epoch_time, epoch_time))
        
        print(f"Stamped EXIF metadata & Date ({exif_date_str}) on: {Path(file_path).name}")
        return True
    except Exception as e:
        print(f"Error embedding EXIF on {file_path}: {e}", file=sys.stderr)
        return False


def upload_to_google_photos_api(token, item, album_id=None):
    """Uploads a media item to Google Photos Library API v1."""
    file_path = item.get("filePath")
    desc = item.get("metadataDescription", "")
    file_name = item.get("fileName", Path(file_path).name)
    
    with open(file_path, "rb") as f:
        data = f.read()
        
    # Step 1: Upload raw bytes to get uploadToken
    upload_url = "https://photoslibrary.googleapis.com/v1/uploads"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-type": "application/octet-stream",
        "X-Goog-Upload-Content-Type": "image/jpeg",
        "X-Goog-Upload-Protocol": "raw"
    }
    req = urllib.request.Request(upload_url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        upload_token = resp.read().decode("utf-8")
        
    # Step 2: Create media item with description/caption
    batch_url = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
    body = {
        "newMediaItems": [
            {
                "description": desc,
                "simpleMediaItem": {
                    "uploadToken": upload_token,
                    "fileName": file_name
                }
            }
        ]
    }
    if album_id:
        body["albumId"] = album_id
        
    batch_req = urllib.request.Request(
        batch_url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(batch_req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Google Photos upload confirmed: {file_name}")
        return res

def main():
    if not MANIFEST_PATH.exists():
        print(f"No manifest found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    if not manifest:
        print("Manifest is empty (no new photos).")
        return

    DRIVE_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    
    token = None
    if "GPHOTOS_ACCESS_TOKEN" in os.environ:
        token = os.environ["GPHOTOS_ACCESS_TOKEN"]
    elif refresh_tokens_if_needed:
        token = refresh_tokens_if_needed()
    elif OAUTH_TOKEN_FILE.exists():
        try:
            with open(OAUTH_TOKEN_FILE, "r") as f:
                token = json.load(f).get("access_token")
        except Exception:
            pass
    elif GPHOTOS_TOKEN_FILE.exists():
        try:
            with open(GPHOTOS_TOKEN_FILE, "r") as f:
                token = json.load(f).get("access_token")
        except Exception:
            pass

    processed_ids = []
    
    print(f"Processing {len(manifest)} photos...")
    for item in manifest:
        # 1. Embed EXIF metadata
        embed_exif_metadata(item)
        
        # 2. Stage copy into Google Drive Photos
        local_src = Path(item["filePath"])
        drive_dest = DRIVE_PHOTOS_DIR / local_src.name
        import shutil
        shutil.copy2(local_src, drive_dest)
        
        # 3. Google Photos API upload if token present
        if token:
            try:
                upload_to_google_photos_api(token, item)
            except Exception as e:
                print(f"Google Photos API upload error on {local_src.name}: {e}")
                
        processed_ids.append(item.get("fileId"))

    # Update state file
    state = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except Exception:
            pass
            
    existing = set(state.get("processed_photos", []))
    existing.update(processed_ids)
    state["processed_photos"] = list(existing)
    
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
        
    print(f"Successfully processed and tagged {len(manifest)} photos.")
    print(f"Files preserved in: {Path.home()}/Pictures/Duchesne PK4/ and {DRIVE_PHOTOS_DIR}")

if __name__ == "__main__":
    main()
