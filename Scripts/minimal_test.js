/**
 * 最小测试脚本 - 只创建基础Widget Blueprint
 */
const net = require('net');

const UE_HOST = '127.0.0.1';
const UE_PORT = 55557;

function sendCommand(commandType, params = {}) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    client.setNoDelay(true);
    client.setTimeout(30000);
    let buffer = '';

    client.connect(UE_PORT, UE_HOST, () => {
      const payload = { type: commandType, params };
      client.write(JSON.stringify(payload) + '\n');
    });

    client.on('data', (data) => {
      buffer += data.toString('utf8');
      try {
        const json = JSON.parse(buffer);
        client.destroy();
        resolve(json);
      } catch {
        // 继续接收
      }
    });

    client.on('timeout', () => {
      client.destroy();
      reject(new Error('超时'));
    });

    client.on('error', (err) => {
      client.destroy();
      reject(err);
    });
  });
}

async function main() {
  console.log('=== 最小测试脚本 ===\n');

  // 步骤 1: 创建 Widget Blueprint
  console.log('1. 创建 Widget Blueprint...');
  try {
    const result = await sendCommand('create_umg_widget_blueprint', { name: 'WBP_TestPanel' });
    console.log('   结果:', JSON.stringify(result, null, 2));
  } catch (err) {
    console.log('   失败:', err.message);
  }

  // 等待
  await new Promise(r => setTimeout(r, 2000));

  // 步骤 2: 尝试添加 VerticalBox（不是Border）
  console.log('\n2. 添加 VerticalBox 到 MainVerticalBox...');
  try {
    const result = await sendCommand('add_vertical_box_to_widget', {
      blueprint_name: 'WBP_TestPanel',
      widget_name: 'MainVerticalBox',
      parent_name: ''  // 尝试添加到根
    });
    console.log('   结果:', JSON.stringify(result, null, 2));
  } catch (err) {
    console.log('   失败:', err.message);
  }

  console.log('\n=== 测试完成 ===');
}

main().catch(err => {
  console.error('错误:', err);
  process.exit(1);
});