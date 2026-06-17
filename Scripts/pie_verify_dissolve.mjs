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
  console.log('start', JSON.stringify(await run('start_pie.py')));
  await sleep(4000);
  await run('sample_burst_runtime_meshes.py'); console.log('=== sample initial');
  console.log('trigger', JSON.stringify(await run('trigger_burst_state_two.py')));
  await sleep(5000); await run('sample_burst_runtime_meshes.py'); console.log('=== sample t+5.0');
  await sleep(1000); await run('sample_burst_runtime_meshes.py'); console.log('=== sample t+6.0');
  await sleep(1500); await run('sample_burst_runtime_meshes.py'); console.log('=== sample t+7.5');
  console.log('stop', JSON.stringify(await run('stop_pie.py')));
})().catch(e => { console.error(e.message); process.exit(1); });
