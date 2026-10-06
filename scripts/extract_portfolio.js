const fs = require('fs');

function browserExtractor() {
  try {
    const allElements = Array.from(document.querySelectorAll('*'));
    const cards = allElements.filter(el => {
      return el.innerText && el.innerText.includes('tagged ');
    });
    
    // Find containers that have direct post content
    const topContainers = cards.filter(c => {
      return !cards.some(other => other !== c && other.contains(c));
    });
    
    return topContainers.map(c => {
      const bgImgs = [];
      c.querySelectorAll('*').forEach(el => {
        const bg = window.getComputedStyle(el).backgroundImage;
        if (bg && bg.includes('cloud.toddleapp.com')) {
          const match = bg.match(/https:\/\/[^"')]+/);
          if (match) bgImgs.push(match[0]);
        }
      });
      
      return {
        text: c.innerText,
        images: Array.from(new Set(bgImgs))
      };
    });
  } catch (err) {
    return { error: err.message, stack: err.stack };
  }
}

async function main() {
  const tabs = await fetch('http://127.0.0.1:9222/json').then(r => r.json());
  const toddleTab = tabs.find(t => t.url.includes('toddle'));
  if (!toddleTab) {
    console.error('No Toddle tab found');
    process.exit(1);
  }

  const ws = new WebSocket(toddleTab.webSocketDebuggerUrl);
  ws.onopen = () => {
    ws.send(JSON.stringify({
      id: 1,
      method: 'Runtime.evaluate',
      params: {
        expression: `(${browserExtractor.toString()})()`,
        returnByValue: true
      }
    }));
  };

  ws.onmessage = (msg) => {
    const data = JSON.parse(msg.data);
    if (data.id === 1) {
      console.log('Result:', JSON.stringify(data.result?.result?.value, null, 2));
      ws.close();
    }
  };
}

main().catch(console.error);
