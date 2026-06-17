/**
 * 逐个测试脚本 - 逐个命令测试找出问题
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

async function testCommand(name, params) {
  try {
    const result = await sendCommand(name, params);
    if (result.error) {
      console.log(`  ${name}: 错误 - ${result.error}`);
    } else {
      console.log(`  ${name}: 成功`);
    }
    return !result.error;
  } catch (err) {
    console.log(`  ${name}: 连接失败 - ${err.message}`);
    return false;
  }
}

async function main() {
  console.log('=== 逐个测试脚本 ===\n');

  // 测试1: 创建 Blueprint
  console.log('1. 创建 WBP_Test...');
  await testCommand('create_umg_widget_blueprint', { name: 'WBP_Test' });
  await new Promise(r => setTimeout(r, 1000));

  // 测试2: 添加 VerticalBox
  console.log('2. 添加 VerticalBox...');
  await testCommand('add_vertical_box_to_widget', {
    blueprint_name: 'WBP_Test',
    widget_name: 'MainVB',
    parent_name: ''
  });
  await new Promise(r => setTimeout(r, 1000));

  // 测试3: 添加 TextBlock
  console.log('3. 添加 TextBlock 到 VerticalBox...');
  await testCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_Test',
    widget_name: 'Label',
    parent_name: 'MainVB',
    text: 'Test'
  });
  await new Promise(r => setTimeout(r, 1000));

  // 测试4: 添加 Slider
  console.log('4. 添加 Slider...');
  await testCommand('add_slider_to_widget', {
    blueprint_name: 'WBP_Test',
    widget_name: 'TestSlider',
    parent_name: 'MainVB',
    min_value: 0.0,
    max_value: 1.0,
    value: 0.5
  });

  console.log('\n=== 测试完成 ===');
}

main().catch(err => {
  console.error('错误:', err);
  process.exit(1);
});