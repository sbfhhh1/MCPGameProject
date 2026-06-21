// 向 UnrealMCP TCP 服务器(55557)发送单条命令并打印 JSON 响应
// 用法: node ue_send.js <command_type> '<json_params>'
const net = require('net');
const [, , type, paramsRaw] = process.argv;
const params = paramsRaw ? JSON.parse(paramsRaw) : {};
const c = net.createConnection(55557, '127.0.0.1', () => {
  c.write(JSON.stringify({ type, params }));
});
let buf = '';
c.on('data', (d) => {
  buf += d.toString('utf8');
  try {
    const j = JSON.parse(buf);
    console.log(JSON.stringify(j));
    c.destroy();
  } catch (_) { /* 等待完整 JSON */ }
});
c.on('error', (e) => { console.error('ERR ' + e.message); process.exit(1); });
c.setTimeout(120000, () => { console.error('ERR timeout'); process.exit(1); });
