import net from 'node:net';

function sendUE(type, params = {}) {
  return new Promise((resolve, reject) => {
    const s = net.createConnection({ host: '127.0.0.1', port: 55557 }, () =>
      s.write(JSON.stringify({ type, params })));
    let d = '';
    s.on('data', c => { d += c.toString(); try { const o = JSON.parse(d); s.destroy(); resolve(o); } catch {} });
    s.on('error', reject);
    setTimeout(() => { s.destroy(); reject(new Error('timeout')); }, 30000);
  });
}

(async () => {
  console.log(JSON.stringify(await sendUE('save_all', {})));
})().catch(e => { console.error(e.message); process.exit(1); });
