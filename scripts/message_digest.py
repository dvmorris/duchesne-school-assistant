import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Union, Dict, Any

ACTION_KEYWORDS = ["please", "remind", "bring", "submit", "return", "rsvp", "deadline", "form", "permission"]

@dataclass
class VeracrossMessage:
    id: str
    sender: str
    subject: str
    timestamp: str
    snippet: str
    is_action_needed: bool
    delivery_type: str = "portal_only"

def parse_iso_or_fallback(ts: str) -> datetime:
    try:
        clean_ts = ts.strip().replace("Z", "+00:00").replace("z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)

def parse_messages_html(html_str: str) -> List[Dict[str, Any]]:
    messages = []
    tag_matches = list(re.finditer(
        r'<div([^>]*class=["\'][^"\']*message[^"\']*["\'][^>]*)>([\s\S]*?)(?:</div>\s*(?=<div[^>]*class=["\'][^"\']*message[^"\']*["\'])|</div>\s*$)',
        html_str,
        re.IGNORECASE
    ))
    if not tag_matches:
        tag_matches = list(re.finditer(
            r'<div([^>]+data-id=["\'][^"\']+["\'][^>]*)>([\s\S]*?)(?:</div>\s*(?=<div[^>]+data-id)|</div>\s*$)',
            html_str,
            re.IGNORECASE
        ))

    for match in tag_matches:
        attrs = match.group(1)
        inner = match.group(2)
        id_match = (
            re.search(r'data-id=["\']([^"\']+)["\']', attrs) or
            re.search(r'id=["\']([^"\']+)["\']', attrs) or
            re.search(r'data-id=["\']([^"\']+)["\']', inner)
        )
        deliv_match = (
            re.search(r'data-delivery-type=["\']([^"\']+)["\']', attrs) or
            re.search(r'data-delivery-type=["\']([^"\']+)["\']', inner)
        )
        sender_match = re.search(r'<span[^>]*class=["\'][^"\']*sender[^"\']*["\'][^>]*>([\s\S]*?)</span>', inner, re.IGNORECASE)
        subject_match = (
            re.search(r'<span[^>]*class=["\'][^"\']*subject[^"\']*["\'][^>]*>([\s\S]*?)</span>', inner, re.IGNORECASE) or
            re.search(r'<h[1-6][^>]*>([\s\S]*?)</h[1-6]>', inner, re.IGNORECASE)
        )
        date_match = (
            re.search(r'<time[^>]*datetime=["\']([^"\']+)["\']', inner, re.IGNORECASE) or
            re.search(r'<span[^>]*class=["\'][^"\']*(?:date|time|timestamp)[^"\']*["\'][^>]*>([\s\S]*?)</span>', inner, re.IGNORECASE)
        )
        body_match = (
            re.search(r'<div[^>]*class=["\'][^"\']*(?:body|snippet|content)[^"\']*["\'][^>]*>([\s\S]*?)</div>', inner, re.IGNORECASE) or
            re.search(r'<p[^>]*>([\s\S]*?)</p>', inner, re.IGNORECASE)
        )

        def clean_html(text: str) -> str:
            return re.sub(r'<[^>]+>', '', text).strip()

        messages.append({
            "id": id_match.group(1) if id_match else "",
            "sender": clean_html(sender_match.group(1)) if sender_match else "Duchesne Faculty",
            "subject": clean_html(subject_match.group(1)) if subject_match else "No Subject",
            "timestamp": clean_html(date_match.group(1)) if date_match else "",
            "body": clean_html(body_match.group(1)) if body_match else "",
            "delivery_type": deliv_match.group(1) if deliv_match else "portal_only"
        })
    return messages

def parse_messages(raw_data: Union[List[Dict[str, Any]], str], max_age_days: int = 14) -> List[VeracrossMessage]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)
    results = []

    if isinstance(raw_data, str):
        raw_str = raw_data.strip()
        if raw_str.startswith("[") or raw_str.startswith("{"):
            try:
                parsed_json = json.loads(raw_str)
                if isinstance(parsed_json, list):
                    raw_data = parsed_json
                elif isinstance(parsed_json, dict) and "messages" in parsed_json:
                    raw_data = parsed_json["messages"]
            except Exception:
                raw_data = parse_messages_html(raw_str)
        else:
            raw_data = parse_messages_html(raw_str)

    if isinstance(raw_data, list):
        for item in raw_data:
            ts_str = item.get("timestamp", "")
            dt = parse_iso_or_fallback(ts_str)
            if dt >= cutoff:
                body = item.get("body", "") or item.get("snippet", "")
                snippet = body[:200].strip()
                searchable_text = f"{item.get('subject', '')} {body} {snippet}".lower()
                is_action = any(k in searchable_text for k in ACTION_KEYWORDS)
                results.append(VeracrossMessage(
                    id=str(item.get("id", "")),
                    sender=item.get("sender", "Duchesne Faculty"),
                    subject=item.get("subject", "No Subject"),
                    timestamp=ts_str,
                    snippet=snippet,
                    is_action_needed=is_action,
                    delivery_type=item.get("delivery_type", "portal_only")
                ))

    return results

def format_messages_digest(messages: List[VeracrossMessage]) -> str:
    if not messages:
        return "No new Veracross messages in the last 14 days."

    lines = ["### 📬 Recent Veracross Messages (Past 14 Days)"]
    for msg in messages:
        action_badge = "[Action Needed] " if msg.is_action_needed else ""
        date_str = msg.timestamp[:10] if len(msg.timestamp) >= 10 else msg.timestamp
        lines.append(f"- **{action_badge}{msg.sender}** — *{date_str}*")
        lines.append(f"  - **Subject:** {msg.subject}")
        lines.append(f"  - **Summary:** {msg.snippet}")
    return "\n".join(lines)
