#!/bin/bash
# Duchesne School Assistant - Weekly Automation Runner
# Runs every Friday at 9:30 AM to check Veracross, Toddle, Nutrislice, and sync to Google Drive, Photos & Calendar

SKILL_DIR="$HOME/.gemini/config/skills/duchesne-school-assistant"
LOG_FILE="$HOME/.gemini/antigravity/duchesne_weekly_sync.log"

echo "=== [$(date)] Starting Duchesne Weekly Automation ===" >> "$LOG_FILE"

# 1. Sync Toddle classroom photos
echo "Syncing Toddle classroom photos..." >> "$LOG_FILE"
node "$SKILL_DIR/scripts/sync_toddle_photos.js" >> "$LOG_FILE" 2>&1 || true

# 2. Tag photos with EXIF metadata and mirror to Google Drive
echo "Tagging photos and mirroring to Drive..." >> "$LOG_FILE"
python3 "$SKILL_DIR/scripts/tag_and_upload_photos.py" >> "$LOG_FILE" 2>&1 || true

# 3. Upload new photos to Google Photos
echo "Uploading photos to Google Photos..." >> "$LOG_FILE"
node "$SKILL_DIR/scripts/upload_photos_browser.js" >> "$LOG_FILE" 2>&1 || true

# 4. Sync upcoming week lunch menu to Google Calendar (at PK4 lunch time: 10:55 AM)
echo "Syncing upcoming week lunch menu to Google Calendar..." >> "$LOG_FILE"
node "$SKILL_DIR/scripts/sync_lunch_to_calendar.js" >> "$LOG_FILE" 2>&1 || true

echo "=== [$(date)] Duchesne Weekly Automation Completed ===" >> "$LOG_FILE"
