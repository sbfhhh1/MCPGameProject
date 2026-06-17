/**
 * 简单诊断脚本 - 测试 MCP 连接
 */
const net = require('net');

const UE_HOST = '127.0.0.1';
const UE_PORT = 55557;

async function test() {
  console.log(`正在连接 ${UE_HOST}:${UE_PORT}...`);

  try {
    const result = await new Promise((resolve, reject) => {
      const client = new net.Socket();
      client.setTimeout(10000);

      client.on('connect', () => {
        console.log('✓ 连接成功!');
        // 发送测试命令
        const payload = { type: 'get_status', params: {} };
        client.write(JSON.stringify(payload) + '\n');
      });

      client.on('data', (data) => {
        console.log('收到响应:', data.toString('utf8'));
        client.destroy();
        resolve('success');
      });

      client.on('timeout', () => {
        console.log('✗ 连接超时');
        client.destroy();
        reject(new Error('超时'));
      });

      client.on('error', (err) => {
        console.log('✗ 连接错误:', err.message);
        reject(err);
      });

      client.connect(UE_PORT, UE_HOST);
    });
  } catch (err) {
    console.log('失败:', err.message);
  }
}

test().then(() => {
  console.log('测试完成');
  process.exit(0);
}).catch(err => {
  console.error('错误:', err);
  process.exit(1);
});