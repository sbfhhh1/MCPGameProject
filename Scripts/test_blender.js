const http = require('http');

async function executeBlenderCode(code) {
  return new Promise((resolve, reject) => {
    let sessionId = '';
    let messageReceived = false;
    
    // SSE 连接
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
              // 发送命令
              sendCommand();
            } else if (data.startsWith('{')) {
              try {
                const json = JSON.parse(data);
                if (json.result || json.error) {
                  messageReceived = true;
                  resolve(json);
                  sseReq.destroy();
                }
              } catch (e) {
                // 解析失败，继续
              }
            }
          }
        }
      });
      res.on('end', () => {
        if (!messageReceived) {
          resolve({ error: 'SSE closed without result' });
        }
      });
    });
    
    sseReq.on('error', reject);
    sseReq.end();
    
    function sendCommand() {
      if (!sessionId) return;
      
      const postData = JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'execute_blender_code',
        params: { code }
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
        // 忽略 POST 响应，响应通过 SSE 接收
      });
      
      msgReq.on('error', reject);
      msgReq.write(postData);
      msgReq.end();
    }
    
    // 超时
    setTimeout(() => {
      sseReq.destroy();
      if (!messageReceived) {
        resolve({ error: 'Timeout waiting for response' });
      }
    }, 30000);
  });
}

// 测试
executeBlenderCode('import bpy; result["ok"] = True; result["version"] = bpy.app.version_string')
  .then(r => console.log('Result:', JSON.stringify(r, null, 2)))
  .catch(e => console.error('Error:', e));
