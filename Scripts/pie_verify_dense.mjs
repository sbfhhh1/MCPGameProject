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
const dir = 'C:/UE_Project/MCPGameProject/Scripts/';
const run = f => sendUE('execute_python_file', { path: dir + f });
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await run('start_pie.py');
  await sleep(3500);
  await run('trigger_burst_state_two.py');
  // dense sample every 0.4s for ~8s covering the whole transition
  for (let i = 0; i < 20; i++) {
    await sleep(400);
    await run('sample_burst_runtime_meshes.py');
  }
  await run('stop_pie.py');
  console.log('done');
})().catch(e => { console.error(e.message); process.exit(1); });
