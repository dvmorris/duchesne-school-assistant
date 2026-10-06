#!/usr/bin/env node
/**
 * Duchesne School Assistant - Lunch Menu to Calendar Sync
 * Fetches upcoming week Lower School lunch menu from Nutrislice,
 * generates an RFC 5545 compliant ICS file with PK4 lunch timing (10:55 AM - 11:25 AM),
 * and imports it directly into Google Calendar via authenticated Chrome CDP session.
 */

const fs = require('fs');
const path = require('path');

const CDP_PORT = 9222;

function getNextMonday(d = new Date()) {
  const date = new Date(d.getTime());
  const day = date.getDay();
  const diff = (day === 0 ? 1 : 8 - day); // If Sunday, next day; otherwise upcoming Monday
  date.setDate(date.getDate() + diff);
  return date;
}

async function fetchMenu(year, month, day) {
  const url = `https://duchesne.api.nutrislice.com/menu/api/weeks/school/lower-school/menu-type/lunch/${year}/${month}/${day}/`;
  const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
  if (!res.ok) {
    throw new Error(`Failed to fetch Nutrislice menu: ${res.status} ${res.statusText}`);
  }
  return await res.json();
}

function generateICS(days) {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Duchesne School Assistant//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VTIMEZONE',
    'TZID:America/Chicago',
    'BEGIN:DAYLIGHT',
    'TZOFFSETFROM:-0600',
    'TZOFFSETTO:-0500',
    'TZNAME:CDT',
    'DTSTART:19700308T020000',
    'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU',
    'END:DAYLIGHT',
    'BEGIN:STANDARD',
    'TZOFFSETFROM:-0500',
    'TZOFFSETTO:-0600',
    'TZNAME:CST',
    'DTSTART:19701101T020000',
    'RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU',
    'END:STANDARD',
    'END:VTIMEZONE'
  ];

  const nowIso = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

  for (const day of days) {
    if (!day.items || day.items.length === 0) continue;
    const dateStr = day.date.replace(/-/g, ''); // YYYYMMDD
    const uid = `duchesne-pk4-lunch-${dateStr}@duchesne.org`;
    const dtstart = `${dateStr}T105500`;
    const dtend = `${dateStr}T112500`;

    const summary = `Duchesne PK4 Lunch: ${day.items[0] || 'Lunch'}`;
    const descItems = day.items.map(item => `• ${item.replace(/,/g, '\\,')}`).join('\\n');
    const description = `Duchesne Lower School PK4 Lunch Menu\\n\\n${descItems}`;

    lines.push(
      'BEGIN:VEVENT',
      `UID:${uid}`,
      `DTSTAMP:${nowIso}`,
      `DTSTART;TZID=America/Chicago:${dtstart}`,
      `DTEND;TZID=America/Chicago:${dtend}`,
      `SUMMARY:${summary}`,
      'LOCATION:Duchesne Academy - Schuhmacher Godfrey Dining Hall',
      `DESCRIPTION:${description}`,
      'END:VEVENT'
    );
  }

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

async function importToGoogleCalendar(icsPath) {
  const tabsRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json`).catch(() => null);
  if (!tabsRes) {
    console.log('Chrome CDP port 9222 not reachable; skipping direct browser import.');
    return false;
  }
  const tabs = await tabsRes.json();
  let calTab = tabs.find(t => t.url && t.url.includes('calendar.google.com') && t.type === 'page');

  if (!calTab) {
    console.log('Opening new Google Calendar tab...');
    const newTabRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?https://calendar.google.com/calendar/u/0/r/settings/export`, { method: 'PUT' });
    calTab = await newTabRes.json();
    await new Promise(r => setTimeout(r, 4000));
  }

  const ws = new WebSocket(calTab.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);

  let id = 1;
  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      const handler = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === msgId) {
          ws.removeEventListener('message', handler);
          if (msg.error) reject(msg.error);
          else resolve(msg.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  try {
    // Navigate to export/import settings
    await send('Page.navigate', { url: 'https://calendar.google.com/calendar/u/0/r/settings/export' });
    await new Promise(r => setTimeout(r, 3500));

    await send('DOM.enable');
    const doc = await send('DOM.getDocument', { depth: -1 });
    const inputNode = await send('DOM.querySelector', {
      nodeId: doc.root.nodeId,
      selector: 'input[type="file"]'
    });

    if (!inputNode || !inputNode.nodeId) {
      console.error('File input not found on Google Calendar import page.');
      ws.close();
      return false;
    }

    await send('DOM.setFileInputFiles', {
      nodeId: inputNode.nodeId,
      files: [icsPath]
    });

    await send('Runtime.evaluate', {
      expression: `
        (() => {
          const input = document.querySelector("input[type=file]");
          if (input) input.dispatchEvent(new Event("change", { bubbles: true }));
        })()
      `
    });

    await new Promise(r => setTimeout(r, 1000));

    // Click Import
    await send('Runtime.evaluate', {
      expression: `
        (() => {
          const btns = Array.from(document.querySelectorAll("button, div[role=button]"));
          const importBtn = btns.find(b => b.innerText?.trim() === "Import");
          if (importBtn) importBtn.click();
        })()
      `
    });

    await new Promise(r => setTimeout(r, 4000));

    const result = await send('Runtime.evaluate', {
      expression: `
        (() => {
          const dialog = document.querySelector("[role=dialog], [role=alertdialog]");
          const text = dialog ? dialog.innerText : "";
          const okBtn = Array.from(document.querySelectorAll("button, div[role=button]")).find(b => b.innerText?.trim() === "OK");
          if (okBtn) okBtn.click();
          return text;
        })()
      `,
      returnByValue: true
    });

    console.log('Calendar import result:', result?.result?.value || 'Import initiated');
    ws.close();
    return true;
  } catch (err) {
    console.error('CDP Google Calendar import error:', err);
    ws.close();
    return false;
  }
}

async function main() {
  const nextMon = getNextMonday();
  const year = nextMon.getFullYear();
  const month = String(nextMon.getMonth() + 1).padStart(2, '0');
  const day = String(nextMon.getDate()).padStart(2, '0');
  const monStr = `${year}-${month}-${day}`;

  console.log(`Fetching Duchesne lunch menu for week of ${monStr}...`);
  const data = await fetchMenu(year, month, day);

  const daysParsed = [];
  const mdLines = ['# Duchesne Lower School Lunch Menu', `### Week of ${monStr}`, ''];

  for (const d of data.days || []) {
    const dDate = d.date;
    const items = (d.menu_items || [])
      .map(m => m.food?.name)
      .filter(Boolean);

    if (items.length > 0) {
      daysParsed.push({ date: dDate, items });
      mdLines.push(`## ${dDate}`);
      items.forEach(it => mdLines.push(`- ${it}`));
      mdLines.push('');
    }
  }

  const driveDir = path.join(process.env.HOME, 'Google Drive', 'Duchesne');
  fs.mkdirSync(driveDir, { recursive: true });

  const mdPath = path.join(driveDir, `Duchesne_Lunch_Menu_${monStr}.md`);
  fs.writeFileSync(mdPath, mdLines.join('\n'));
  console.log(`Saved Markdown menu to: ${mdPath}`);

  const icsPath = path.join(driveDir, `Duchesne_Lunch_Menu_${monStr}.ics`);
  const icsContent = generateICS(daysParsed);
  fs.writeFileSync(icsPath, icsContent);
  console.log(`Saved ICS calendar to: ${icsPath} (${daysParsed.length} days)`);

  await importToGoogleCalendar(icsPath);

  // Update state file
  const statePath = path.join(process.env.HOME, '.gemini', 'antigravity', 'duchesne_state.json');
  if (fs.existsSync(statePath)) {
    try {
      const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
      state.last_lunch_sync = new Date().toISOString();
      if (!state.uploaded_files.includes(mdPath)) state.uploaded_files.push(mdPath);
      if (!state.uploaded_files.includes(icsPath)) state.uploaded_files.push(icsPath);
      fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
    } catch (e) {
      console.warn('Could not update state file:', e.message);
    }
  }
}

main().catch(console.error);
