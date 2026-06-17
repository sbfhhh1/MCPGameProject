/**
 * WBP_GNControlPanel 创建脚本
 * 使用 MCP 命令自动构建渐变色盒子运行时控制面板
 */
const net = require('net');

const UE_HOST = '127.0.0.1';
const UE_PORT = 55557;

function sendCommand(commandType, params = {}) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    client.setNoDelay(true);
    client.setTimeout(20000);
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

async function runCommand(name, params, delay = 500) {
  try {
    console.log(`  → ${name}...`);
    const result = await sendCommand(name, params);
    await new Promise(r => setTimeout(r, delay));

    if (result.error) {
      console.log(`    ⚠ ${result.error}`);
      return false;
    }
    console.log(`    ✓ 完成`);
    return true;
  } catch (err) {
    console.log(`    ✗ 错误: ${err.message}`);
    return false;
  }
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║      WBP_GNControlPanel 控制面板创建脚本                  ║');
  console.log('╚══════════════════════════════════════════════════════════╝\n');

  console.log('正在连接 Unreal Engine MCP...\n');

  // 步骤 1: 创建 Widget Blueprint
  console.log('【步骤 1】创建 Widget Blueprint');
  const bpCreated = await runCommand('create_umg_widget_blueprint', { name: 'WBP_GNControlPanel' });
  if (!bpCreated) {
    console.log('\n⚠ Widget Blueprint 可能已存在，继续添加子组件...\n');
  }

  // 步骤 2: 添加主容器
  console.log('\n【步骤 2】添加主容器');
  await runCommand('add_border_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'MainBorder',
    parent_name: 'CanvasPanel_0',
    color_r: 0.08,
    color_g: 0.08,
    color_b: 0.12,
    color_a: 0.95,
    padding_left: 15,
    padding_top: 15,
    padding_right: 15,
    padding_bottom: 15
  });

  await runCommand('add_vertical_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'MainVerticalBox',
    parent_name: 'MainBorder'
  });

  // 步骤 3: 添加标题
  console.log('\n【步骤 3】添加标题');
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'HeaderBox',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'IconText',
    parent_name: 'HeaderBox',
    text: '🎯',
    position: [10, 10]
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'TitleText',
    parent_name: 'HeaderBox',
    text: 'GradientBox 动画控制',
    position: [50, 10]
  });

  // 设置标题样式
  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'TitleText',
    widget_type: 'TextBlock',
    font_size: 18,
    font_color: '#E0E0E0'
  });

  // 步骤 4: 添加"呼吸动画"分组
  console.log('\n【步骤 4】添加呼吸动画分组');
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionHeader_Motion',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionTitle_Motion',
    parent_name: 'SectionHeader_Motion',
    text: '▼ 呼吸动画',
    position: [0, 5]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionTitle_Motion',
    widget_type: 'TextBlock',
    font_size: 14,
    font_color: '#A0A0FF'
  });

  // 幅度 Slider
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'AmplitudeRow',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'AmplitudeLabel',
    parent_name: 'AmplitudeRow',
    text: '幅度:',
    position: [0, 0]
  });

  await runCommand('add_slider_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'AmplitudeSlider',
    parent_name: 'AmplitudeRow',
    min_value: 0.0,
    max_value: 1.0,
    step_size: 0.01,
    value: 1.0
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'AmplitudeValue',
    parent_name: 'AmplitudeRow',
    text: '1.00',
    position: [300, 0]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'AmplitudeLabel',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#B0B0B0'
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'AmplitudeValue',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#FFFFFF'
  });

  // 速度 Slider
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SpeedRow',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SpeedLabel',
    parent_name: 'SpeedRow',
    text: '速度:',
    position: [0, 0]
  });

  await runCommand('add_slider_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SpeedSlider',
    parent_name: 'SpeedRow',
    min_value: 0.0,
    max_value: 4.0,
    step_size: 0.05,
    value: 1.0
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SpeedValue',
    parent_name: 'SpeedRow',
    text: '1.00',
    position: [300, 0]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SpeedLabel',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#B0B0B0'
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SpeedValue',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#FFFFFF'
  });

  // 平滑度 Slider
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SmoothnessRow',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SmoothnessLabel',
    parent_name: 'SmoothnessRow',
    text: '平滑度:',
    position: [0, 0]
  });

  await runCommand('add_slider_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SmoothnessSlider',
    parent_name: 'SmoothnessRow',
    min_value: 0.0,
    max_value: 1.0,
    step_size: 0.01,
    value: 0.55
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SmoothnessValue',
    parent_name: 'SmoothnessRow',
    text: '0.55',
    position: [300, 0]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SmoothnessLabel',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#B0B0B0'
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SmoothnessValue',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#FFFFFF'
  });

  // 步骤 5: 添加"性能设置"分组
  console.log('\n【步骤 5】添加性能设置分组');
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionHeader_Perf',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionTitle_Perf',
    parent_name: 'SectionHeader_Perf',
    text: '▼ 性能设置',
    position: [0, 5]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionTitle_Perf',
    widget_type: 'TextBlock',
    font_size: 14,
    font_color: '#A0A0FF'
  });

  // FPS Slider
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FPSRow',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FPSLabel',
    parent_name: 'FPSRow',
    text: '最大FPS:',
    position: [0, 0]
  });

  await runCommand('add_slider_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FPSSilder',
    parent_name: 'FPSRow',
    min_value: 1.0,
    max_value: 120.0,
    step_size: 1.0,
    value: 60.0
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FPSValue',
    parent_name: 'FPSRow',
    text: '60',
    position: [300, 0]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FPSLabel',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#B0B0B0'
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FPSValue',
    widget_type: 'TextBlock',
    font_size: 13,
    font_color: '#FFFFFF'
  });

  // 快速网格 Checkbox
  await runCommand('add_checkbox_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'FastMeshCheckBox',
    parent_name: 'MainVerticalBox',
    text: '快速动态网格',
    is_checked: true
  });

  // 法线重算 Checkbox
  await runCommand('add_checkbox_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'NormalsCheckBox',
    parent_name: 'MainVerticalBox',
    text: '重算法线',
    is_checked: false
  });

  // 步骤 6: 添加"材质同步"分组
  console.log('\n【步骤 6】添加材质同步分组');
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionHeader_Material',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionTitle_Material',
    parent_name: 'SectionHeader_Material',
    text: '▼ 材质同步',
    position: [0, 5]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'SectionTitle_Material',
    widget_type: 'TextBlock',
    font_size: 14,
    font_color: '#A0A0FF'
  });

  // 相位差指示器
  await runCommand('add_horizontal_box_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'PhaseIndicator',
    parent_name: 'MainVerticalBox'
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'BlueIcon',
    parent_name: 'PhaseIndicator',
    text: '🔵',
    position: [0, 0]
  });

  await runCommand('add_text_block_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'PhaseLabel',
    parent_name: 'PhaseIndicator',
    text: '蓝 | 粉 相位差: 180°',
    position: [30, 0]
  });

  await runCommand('set_widget_style', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'PhaseLabel',
    widget_type: 'TextBlock',
    font_size: 12,
    font_color: '#909090'
  });

  // 反向动画 Checkbox
  await runCommand('add_checkbox_to_widget', {
    blueprint_name: 'WBP_GNControlPanel',
    widget_name: 'ReverseCheckBox',
    parent_name: 'MainVerticalBox',
    text: '启用反向动画',
    is_checked: true
  });

  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║              WBP_GNControlPanel 创建完成！                 ║');
  console.log('╚══════════════════════════════════════════════════════════╝\n');
  console.log('下一步:');
  console.log('1. 在 UE Editor 中打开 Content/Widgets/WBP_GNControlPanel');
  console.log('2. 在 Event Graph 中绑定滑块事件到 BlenderGNRuntimePanelWidget 函数');
  console.log('3. 添加到 Viewport 进行测试\n');
}

main().catch(err => {
  console.error('脚本执行失败:', err.message);
  process.exit(1);
});