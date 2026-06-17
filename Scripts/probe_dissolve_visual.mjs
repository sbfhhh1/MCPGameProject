import net from 'node:net';
import { writeFileSync } from 'node:fs';

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
const sleep = ms => new Promise(r => setTimeout(r, ms));
const valFile = 'C:/UE_Project/MCPGameProject/Saved/yf_probe_value.txt';

(async () => {
  for (const v of ['0.0', '0.5', '1.0']) {
    writeFileSync(valFile, v);
    await sendUE('execute_python_file', { path: 'C:/UE_Project/MCPGameProject/Scripts/probe_set_yf.py' });
    await sleep(1500);
    const r = await sendUE('take_screenshot', { filepath: `C:/UE_Project/MCPGameProject/Saved/yf_d${v}.png` });
    console.log('d' + v, JSON.stringify(r));
  }
})().catch(e => { console.error(e.message); process.exit(1); });
