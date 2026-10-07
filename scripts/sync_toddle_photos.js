/**
 * Script to extract Toddle portfolio posts and download photos with metadata.
 */
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(process.env.HOME, 'Pictures', 'Duchesne PK4');
const STATE_FILE = path.join(process.env.HOME, '.gemini', 'antigravity', 'duchesne_state.json');

async function getCDPConnection() {
  const tabs = await fetch('http://127.0.0.1:9222/json').then(r => r.json());
  const toddleTab = tabs.find(t => t.url && t.url.includes('toddle'));
  if (!toddleTab) {
    throw new Error('No Toddle tab found in Chrome at port 9222');
  }
  return {
    wsUrl: toddleTab.webSocketDebuggerUrl,
    tabId: toddleTab.id
  };
}

function parseToddleDate(dateStr) {
  const s = (dateStr || '').trim();
  const months = {
    jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06',
    jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12'
  };

  // Match e.g. "27 Aug 2026, 10.27 am", "8 Sep 2026, 8.19 am", "4 Sep 2026, 2.57 pm"
  const m = s.match(/(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4}),?\s+(\d{1,2})[.:](\d{2})\s*(am|pm)/i);
  if (m) {
    const day = m[1].padStart(2, '0');
    const mon = months[m[2].toLowerCase()] || '09';
    const year = m[3];
    let hour = parseInt(m[4], 10);
    const min = m[5].padStart(2, '0');
    const ampm = m[6].toLowerCase();
    if (ampm === 'pm' && hour !== 12) hour += 12;
    if (ampm === 'am' && hour === 12) hour = 0;
    const hourStr = String(hour).padStart(2, '0');
    return {
      iso: `${year}-${mon}-${day}T${hourStr}:${min}:00`,
      exif: `${year}:${mon}:${day} ${hourStr}:${min}:00`,
      filePrefix: `${year}${mon}${day}_${hourStr}${min}`
    };
  }

  // Relative times: e.g. "53 m ago", "2 h ago", "1 d ago"
  let targetDate = new Date();
  const relMin = s.match(/(\d+)\s*m\s*ago/i);
  const relHour = s.match(/(\d+)\s*h\s*ago/i);
  const relDay = s.match(/(\d+)\s*d\s*ago/i);
  if (relMin) {
    targetDate = new Date(Date.now() - parseInt(relMin[1], 10) * 60000);
  } else if (relHour) {
    targetDate = new Date(Date.now() - parseInt(relHour[1], 10) * 3600000);
  } else if (relDay) {
    targetDate = new Date(Date.now() - parseInt(relDay[1], 10) * 86400000);
  }

  const y = targetDate.getFullYear();
  const mo = String(targetDate.getMonth() + 1).padStart(2, '0');
  const d = String(targetDate.getDate()).padStart(2, '0');
  const h = String(targetDate.getHours()).padStart(2, '0');
  const mi = String(targetDate.getMinutes()).padStart(2, '0');
  const sec = String(targetDate.getSeconds()).padStart(2, '0');

  return {
    iso: `${y}-${mo}-${d}T${h}:${mi}:${sec}`,
    exif: `${y}:${mo}:${d} ${h}:${mi}:${sec}`,
    filePrefix: `${y}${mo}${d}_${h}${mi}`
  };
}

function browserExtractPosts() {
  try {
    const cards = Array.from(document.querySelectorAll('[class*="SubjectJournalCard__cardContainerV2"]'));
    return cards.map((card, idx) => {
      const text = card.innerText || '';
      const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

      // Teacher
      const teacherEl = card.querySelector('[class*="SubjectJournalCard__taggedAssesmentMessageTextV2"]');
      let teacher = 'Teacher';
      if (teacherEl) {
        teacher = teacherEl.innerText.replace(/tagged\s+[^,\n]+,\s*[^<\n]+/i, '').trim();
      } else {
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('tagged ')) {
            teacher = lines[i].replace(/tagged\s+[^,\n]+,\s*[^<\n]+/i, '').trim();
            break;
          }
        }
      }

      // Time string
      let timeStr = '';
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.includes('ago') || line.includes('Aug') || line.includes('Sep') || line.match(/\d{1,2}\s+[A-Za-z]+\s+\d{4}/)) {
          timeStr = line;
          break;
        }
      }

      // Caption
      const captionEl = card.querySelector('[class*="postCaptionText"]');
      let caption = captionEl ? captionEl.innerText.trim() : '';
      if (!caption) {
        const timeIdx = lines.indexOf(timeStr);
        if (timeIdx !== -1 && lines[timeIdx + 1] && !lines[timeIdx + 1].includes('/')) {
          caption = lines[timeIdx + 1];
        } else {
          caption = 'Class activity';
        }
      }

      const bgImgs = [];
      card.querySelectorAll('*').forEach(el => {
        const bg = window.getComputedStyle(el).backgroundImage;
        if (bg && bg.includes('cloud.toddleapp.com')) {
          const match = bg.match(/https:\/\/[^"')]+/);
          if (match) bgImgs.push(match[0]);
        }
        if (el.tagName === 'IMG' && el.src && el.src.includes('cloud.toddleapp.com')) {
          bgImgs.push(el.src);
        }
      });

      return {
        id: `post_${idx}`,
        teacher: teacher,
        student: process.env.DUCHESNE_STUDENT_NAME || 'Student',
        caption: caption,
        timeString: timeStr,
        images: Array.from(new Set(bgImgs))
      };
    });
  } catch (e) {
    return { error: e.message };
  }
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const { wsUrl } = await getCDPConnection();
  
  const ws = new WebSocket(wsUrl);
  await new Promise(resolve => ws.onopen = resolve);

  const forceAll = process.argv.includes('--all');
  let state = {};
  if (fs.existsSync(STATE_FILE)) {
    try {
      state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    } catch (e) {}
  }
  const processedSet = new Set(state.processed_photos || []);

  let idCounter = 1;
  function sendCdp(method, params = {}) {
    return new Promise(resolve => {
      const msgId = idCounter++;
      const handler = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === msgId) {
          ws.removeEventListener('message', handler);
          resolve(msg.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  // Ensure navigated to journal
  await sendCdp('Page.navigate', { url: 'https://web.toddleapp.com/platform/116643011487614044/courses/404156575888982361/journal' });
  await new Promise(r => setTimeout(r, 4000));

  // Scroll to ensure cards are in DOM
  for (let s = 0; s < 5; s++) {
    await sendCdp('Runtime.evaluate', { expression: 'window.scrollBy(0, 1500)' });
    await new Promise(r => setTimeout(r, 600));
  }

  // 1. Get Toddle cookies
  const cookiesPromise = sendCdp('Network.getCookies', { urls: ['https://web.toddleapp.com', 'https://cloud.toddleapp.com'] });
  const cookiesResult = await cookiesPromise;
  const cookies = cookiesResult?.cookies || [];
  const cookieHeader = cookies.map(c => `${c.name}=${c.value}`).join('; ');

  // 2. Extract posts data from DOM
  const postsResult = await sendCdp('Runtime.evaluate', {
    expression: `(${browserExtractPosts.toString()})()`,
    returnByValue: true
  });

  const rawPosts = postsResult?.result?.value || [];
  ws.close();

  const downloadedMedia = [];

  for (const post of rawPosts) {
    const parsedDate = parseToddleDate(post.timeString);
    console.log(`Processing post: "${post.caption}" by ${post.teacher} [Date: ${parsedDate.exif}] (${post.images.length} images)`);

    for (let i = 0; i < post.images.length; i++) {
      const imgUrl = post.images[i];
      const originalUrl = imgUrl.includes('/https://') ? imgUrl.split('/https://')[1] ? 'https://' + imgUrl.split('/https://')[1] : imgUrl : imgUrl;
      const fileId = path.basename(originalUrl.split('?')[0]);

      const cleanCaption = post.caption.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
      const fileName = `Duchesne_${parsedDate.filePrefix}_${cleanCaption}_${i + 1}.jpeg`;
      const filePath = path.join(OUTPUT_DIR, fileName);

      if (!forceAll && processedSet.has(fileId)) {
        console.log(`  Skipping already processed photo: ${fileId} (${fileName})`);
        continue;
      }

      let buffer = null;
      if (fs.existsSync(filePath)) {
        buffer = fs.readFileSync(filePath);
      } else {
        try {
          const resp = await fetch(imgUrl, {
            headers: {
              'Cookie': cookieHeader,
              'Referer': 'https://web.toddleapp.com/'
            }
          });
          if (resp.ok) {
            buffer = Buffer.from(await resp.arrayBuffer());
            fs.writeFileSync(filePath, buffer);
            console.log(`  Downloaded: ${fileName} (${buffer.length} bytes)`);
          }
        } catch (err) {
          console.error(`  Error downloading ${imgUrl}:`, err.message);
        }
      }

      if (buffer) {
        downloadedMedia.push({
          filePath,
          fileName,
          fileId,
          caption: post.caption,
          teacher: post.teacher,
          student: post.student,
          timeString: post.timeString,
          exifDate: parsedDate.exif,
          isoDate: parsedDate.iso,
          metadataDescription: `[Duchesne Academy - PK4] ${post.caption} | Teacher: ${post.teacher} | Student: ${post.student} | Toddle: ${post.timeString}`
        });
      }
    }
  }

  // Write updated metadata manifest for Python EXIF stamper
  const manifestPath = path.join(OUTPUT_DIR, 'download_manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(downloadedMedia, null, 2));
  console.log(`Total ${downloadedMedia.length} photos staged with exact dates. Manifest saved to ${manifestPath}`);
}

main().catch(console.error);
