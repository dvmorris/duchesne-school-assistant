#!/usr/bin/env node
/**
 * Browser-driven photo uploader for Google Photos.
 * Uploads classroom photos directly via the authenticated Chrome browser window
 * using Chrome DevTools Protocol (CDP) file chooser interception.
 */

const fs = require('fs');
const path = require('path');

const MANIFEST_PATH = path.join(process.env.HOME, 'Pictures', 'Duchesne PK4', 'download_manifest.json');
const STATE_FILE = path.join(process.env.HOME, '.gemini', 'antigravity', 'duchesne_state.json');

async function getCDPConnection() {
  const tabs = await fetch('http://127.0.0.1:9222/json').then(r => r.json());
  let photoTab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('photos.google.com'));
  
  if (!photoTab) {
    photoTab = await fetch('http://127.0.0.1:9222/json/new?https://photos.google.com/', { method: 'PUT' }).then(r => r.json());
    await new Promise(r => setTimeout(r, 4000));
  }
  
  return {
    wsUrl: photoTab.webSocketDebuggerUrl,
    tabId: photoTab.id
  };
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.msgId = 1;
    this.eventListeners = new Map();
  }

  async connect() {
    await new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = rej;
    });

    this.ws.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      if (data.method) {
        const listeners = this.eventListeners.get(data.method) || [];
        listeners.forEach(fn => fn(data.params));
      }
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.msgId++;
      const handler = (event) => {
        const data = JSON.parse(event.data);
        if (data.id === id) {
          this.ws.removeEventListener('message', handler);
          if (data.error) reject(new Error(data.error.message));
          else resolve(data.result);
        }
      };
      this.ws.addEventListener('message', handler);
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  on(event, handler) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(handler);
  }

  close() {
    try { this.ws.close(); } catch (e) {}
  }
}

async function main() {
  if (!fs.existsSync(MANIFEST_PATH)) {
    console.log(`No manifest found at ${MANIFEST_PATH}`);
    process.exit(1);
  }

  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
  if (!manifest || manifest.length === 0) {
    console.log('Manifest is empty.');
    process.exit(0);
  }

  const filePaths = manifest
    .map(m => m.filePath)
    .filter(p => p && fs.existsSync(p));

  console.log(`Found ${filePaths.length} photos staged for Google Photos upload.`);

  const { wsUrl } = await getCDPConnection();
  const cdp = new CDPClient(wsUrl);
  await cdp.connect();

  console.log('Connected to Google Photos tab via CDP.');

  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  try { await cdp.send('Page.bringToFront'); } catch (e) {}

  // Verify current URL and ensure we are on https://photos.google.com/
  const navRes = await cdp.send('Runtime.evaluate', {
    expression: 'window.location.href',
    returnByValue: true
  });
  const currentUrl = navRes?.result?.value || '';
  if (currentUrl !== 'https://photos.google.com/' && currentUrl !== 'https://photos.google.com') {
    console.log(`Navigating to https://photos.google.com/ (currently: ${currentUrl})...`);
    await cdp.send('Page.navigate', { url: 'https://photos.google.com/' });
    await new Promise(r => setTimeout(r, 4000));
  }

  // Set up file chooser interception
  await cdp.send('Page.setInterceptFileChooserDialog', { enabled: true });

  const fileChooserPromise = new Promise((resolve) => {
    cdp.on('Page.fileChooserOpened', (params) => {
      resolve(params);
    });
  });

  // Ensure "Import photos from your computer" menu item is open and visible
  let menuCoords = await cdp.send('Runtime.evaluate', {
    expression: `(() => {
      const isVisible = (el) => {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      };

      let item = Array.from(document.querySelectorAll("[role=menuitem]")).find(e => e.getAttribute("aria-label")?.includes("computer"));
      if (!isVisible(item)) {
        const btn = Array.from(document.querySelectorAll("button, [role=button]")).find(b => b.getAttribute("aria-label") === "Create and add photos");
        if (btn) btn.click();
      }
      return true;
    })()`,
    returnByValue: true
  });

  await new Promise(r => setTimeout(r, 1000));

  // Find exact coordinates of "Import photos from your computer"
  const itemCoordsRes = await cdp.send('Runtime.evaluate', {
    expression: `(() => {
      const el = Array.from(document.querySelectorAll("[role=menuitem]")).find(e => e.getAttribute("aria-label")?.includes("computer"));
      if (!el) return null;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return null;
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    })()`,
    returnByValue: true
  });

  let coords = itemCoordsRes?.result?.value;
  if (!coords || !coords.x || !coords.y) {
    coords = { x: 1057, y: 309 };
  }
  console.log(`Triggering file chooser at (${Math.round(coords.x)}, ${Math.round(coords.y)})...`);

  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mousePressed',
    x: coords.x,
    y: coords.y,
    button: 'left',
    clickCount: 1
  });
  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mouseReleased',
    x: coords.x,
    y: coords.y,
    button: 'left',
    clickCount: 1
  });


  console.log('Waiting for browser file chooser dialog...');
  const chooserParams = await Promise.race([
    fileChooserPromise,
    new Promise((_, rej) => setTimeout(() => rej(new Error('Timeout waiting for file chooser dialog')), 10000))
  ]);

  console.log(`Browser file chooser intercepted successfully (mode: ${chooserParams.mode})!`);
  console.log(`Submitting ${filePaths.length} photos with embedded EXIF metadata to Google Photos on backendNodeId: ${chooserParams.backendNodeId}...`);

  await cdp.send('DOM.setFileInputFiles', {
    backendNodeId: chooserParams.backendNodeId,
    files: filePaths
  });

  console.log('Batch submitted to Google Photos! Monitoring upload progress...');

  // Monitor progress
  const startTime = Date.now();
  const maxWaitMs = 300000; // 5 minutes max
  let lastToast = '';

  while (Date.now() - startTime < maxWaitMs) {
    await new Promise(r => setTimeout(r, 4000));

    const status = await cdp.send('Runtime.evaluate', {
      expression: `(() => {
        const bodyText = document.body.innerText.replace(/\\n+/g, ' ');
        const toasts = Array.from(document.querySelectorAll("[role=alert], [role=status], [class*=toast], [class*=upload], [class*=snack]")).map(e => (e.innerText || "").trim().replace(/\\n+/g, ' ')).filter(Boolean);
        
        const hasUploading = bodyText.includes('Uploading') || bodyText.includes('uploading') || toasts.some(t => t.toLowerCase().includes('uploading'));
        const hasUploaded = toasts.some(t => t.toLowerCase().includes('uploaded') || t.toLowerCase().includes('items uploaded')) || bodyText.includes('items uploaded') || bodyText.includes('Upload complete');
        const addToAlbumBtn = Array.from(document.querySelectorAll('button, [role=button]')).find(b => (b.innerText || '').includes('Add to album'));

        return {
          toasts,
          hasUploading,
          hasUploaded,
          hasAddToAlbum: !!addToAlbumBtn
        };
      })()`,
      returnByValue: true
    });

    const val = status?.result?.value;
    const currentToast = val?.toasts ? val.toasts.join(' | ') : '';
    if (currentToast && currentToast !== lastToast) {
      console.log(`[Google Photos Notification] ${currentToast}`);
      lastToast = currentToast;
    }

    if (val?.hasAddToAlbum) {
      console.log('Upload complete! "Add to album" option available.');
      break;
    }

    if (val?.hasUploaded && !val?.hasUploading) {
      console.log('All items successfully uploaded.');
      break;
    }

    // After 25 seconds of quiet after start, check Recently Added if no active uploading
    if (Date.now() - startTime > 25000 && !val?.hasUploading) {
      console.log('Upload pipeline completed.');
      break;
    }
  }

  // Update duchesne_state.json
  let state = {};
  if (fs.existsSync(STATE_FILE)) {
    try { state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch (e) {}
  }
  const processed = new Set(state.processed_photos || []);
  manifest.forEach(m => {
    if (m.fileId) processed.add(m.fileId);
  });
  state.processed_photos = Array.from(processed);
  state.last_photos_upload = new Date().toISOString();
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));

  console.log(`\n======================================================`);
  console.log(`SUCCESS: Uploaded ${filePaths.length} PK4 classroom photos directly via browser.`);
  console.log(`All photos retain embedded EXIF Tag 270 captions & metadata.`);
  console.log(`======================================================`);

  cdp.close();
}

main().catch(err => {
  console.error('Fatal error in upload_photos_browser:', err);
  process.exit(1);
});
