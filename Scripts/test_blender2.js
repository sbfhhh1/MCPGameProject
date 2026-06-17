const http = require('http');

async function executeBlenderCode(code) {
  return new Promise((resolve, reject) => {
    let sessionId = '';
    
    const sseReq = http.request({
      hostname: '127.0.0.1',
      port: 7451,
      path: '/sse',
      method: 'GET',
      headers: { 'Accept': 'text/event-stream' }
    }, (res) => {
      let buffer = '';
      res.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          if (line.startsWith('data:')) {
            const data = line.substring(5).trim();
            if (data.startsWith('/messages')) {
              const url = new URL('http://localhost' + data);
              sessionId = url.searchParams.get('sessionId');
              console.log('Got session:', sessionId);
              sendCommand();
            } else if (data) {
              try {
                const json = JSON.parse(data);
                console.log('SSE event:', JSON.stringify(json));
                if (json.id === 1) {
                  resolve(json);
                  sseReq.destroy();
                }
              } catch (e) {}
            }
          }
        }
      });
      res.on('end', () => resolve({ error: 'SSE closed' }));
    });
    
    sseReq.on('error', reject);
    sseReq.end();
    
    function sendCommand() {
      if (!sessionId) return;
      
      // 尝试不同的格式
      const postData = JSON.stringify({
        type: 'execute',
        code: code
      });
      
      const msgReq = http.request({
        hostname: '127.0.0.1',
        port: 7451,
        path: '/messages?sessionId=' + sessionId,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        }
      }, (res) => {
        console.log('POST status:', res.statusCode);
      });
      
      msgReq.on('error', reject);
      msgReq.write(postData);
      msgReq.end();
    }
    
    setTimeout(() => {
      sseReq.destroy();
      resolve({ error: 'Timeout' });
    }, 30000);
  });
}

executeBlenderCode('import bpy; result["ok"] = True')
  .then(r => console.log('Result:', JSON.stringify(r, null, 2)))
  .catch(e => console.error('Error:', e));
