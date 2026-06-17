import net from 'node:net';

function ping() {
  return new Promise(resolve => {
    const s = net.createConnection({ host: '127.0.0.1', port: 55557 }, () => {
      s.write(JSON.stringify({ type: 'execute_python_file', params: { path: 'C:/UE_Project/MCPGameProject/Scripts/ping_noop.py' } }));
    });
    let d = '';
    s.on('data', c => { d += c.toString(); try { const o = JSON.parse(d); s.destroy(); resolve(o.status === 'success'); } catch {} });
    s.on('error', () => resolve(false));
    setTimeout(() => { s.destroy(); resolve(false); }, 4000);
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  for (let i = 0; i < 50; i++) {
    if (await ping()) { console.log('UE_READY'); process.exit(0); }
    await sleep(6000);
  }
  console.log('UE_NOT_READY');
  process.exit(1);
})();
