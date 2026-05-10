/**
 * UE 命令工具 - 通过 TCP 直接向 UnrealMCP 插件发送命令
 * 绕过 MCP 桥接，支持所有 UE 插件命令
 */
const net = require('net');

const UE_HOST = '127.0.0.1';
const UE_PORT = 55557;

function sendCommand(commandType, params = {}) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    client.setNoDelay(true);
    client.setTimeout(15000);
    let buffer = '';
    let settled = false;

    const settleOnce = (fn, value) => {
      if (settled) return;
      settled = true;
      try { client.destroy(); } catch {}
      fn(value);
    };

    client.connect(UE_PORT, UE_HOST, () => {
      const payload = { type: commandType, params };
      client.write(JSON.stringify(payload));
    });

    client.on('data', (data) => {
      buffer += data.toString('utf8');
      try {
        const json = JSON.parse(buffer);
        settleOnce(resolve, json);
      } catch {}
    });

    client.on('timeout', () => {
      settleOnce(reject, new Error(`连接虚幻引擎超时 (端口 ${UE_PORT})`));
    });

    client.on('error', (err) => {
      settleOnce(reject, err);
    });
  });
}

async function main() {
  const [,, command, ...rest] = process.argv;

  if (!command) {
    console.log('用法: node ue_command.js <命令> [参数JSON]');
    console.log('示例:');
    console.log('  node ue_command.js get_actors_in_level');
    console.log('  node ue_command.js spawn_actor {"type":"StaticMeshActor","name":"MySphere"}');
    console.log('  node ue_command.js delete_actor {"name":"Landscape_UAID_..."}');
    console.log('  node ue_command.js set_actor_property {"name":"MySphere","property_name":"StaticMeshComponent.StaticMesh","property_value":"/Engine/BasicShapes/Sphere.Sphere"}');
    process.exit(1);
  }

  let params = {};
  if (rest.length > 0) {
    try {
      params = JSON.parse(rest.join(' '));
    } catch (e) {
      console.error('参数解析错误:', e.message);
      process.exit(1);
    }
  }

  try {
    const result = await sendCommand(command, params);
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('错误:', err.message);
    process.exit(1);
  }
}

main();
