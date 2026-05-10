const net = require('net');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

// 虚幻引擎 TCP 服务器配置
const UE_HOST = '127.0.0.1';
const UE_PORT = 55557;

const server = new Server({
  name: "unreal-engine-mcp",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {}
  }
});

// 定义向 AI 暴露的虚幻引擎工具
const TOOLS = [
  // ===== 场景查询 =====
  {
    name: "get_actors_in_level",
    description: "获取当前关卡中所有 Actor 的列表和基本属性",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "find_actors_by_name",
    description: "按名称搜索 Actor",
    inputSchema: {
      type: "object",
      properties: {
        name_pattern: { type: "string", description: "名称关键词" }
      },
      required: ["name_pattern"]
    }
  },
  {
    name: "get_actor_properties",
    description: "获取指定 Actor 的详细属性",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Actor 名称" }
      },
      required: ["name"]
    }
  },

  // ===== Actor 操作 =====
  {
    name: "spawn_actor",
    description: "在关卡中创建一个新的 Actor（支持 StaticMeshActor / PointLight / SpotLight / DirectionalLight / CameraActor / SphereReflectionCapture）",
    inputSchema: {
      type: "object",
      properties: {
        type: { type: "string", description: "Actor 类型 (如 StaticMeshActor)" },
        name: { type: "string", description: "Actor 名称 (唯一)" },
        location: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } },
        rotation: { type: "object", properties: { pitch: { type: "number" }, yaw: { type: "number" }, roll: { type: "number" } } },
        scale: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } }
      },
      required: ["type", "name"]
    }
  },
  {
    name: "delete_actor",
    description: "删除场景中指定名称的 Actor",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "要删除的 Actor 名称" }
      },
      required: ["name"]
    }
  },
  {
    name: "set_actor_transform",
    description: "设置指定 Actor 的位置、旋转和缩放",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string" },
        location: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } },
        rotation: { type: "object", properties: { pitch: { type: "number" }, yaw: { type: "number" }, roll: { type: "number" } } },
        scale: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } }
      },
      required: ["name"]
    }
  },
  {
    name: "set_actor_property",
    description: "设置 Actor 的属性（如材质、灯光颜色等）",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Actor 名称" },
        property_name: { type: "string", description: "属性名（如 StaticMeshComponent.Material[0]）" },
        property_value: { type: "object", description: "属性值" }
      },
      required: ["name", "property_name", "property_value"]
    }
  },
  {
    name: "focus_viewport",
    description: "将视口聚焦到指定 Actor",
    inputSchema: {
      type: "object",
      properties: {
        actor_name: { type: "string", description: "Actor 名称（可选，不指定则聚焦整体场景）" }
      }
    }
  },

  // ===== 蓝图操作 =====
  {
    name: "create_blueprint",
    description: "创建一个新的蓝图资产（保存到 /Game/Blueprints/）",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "蓝图名称" },
        parent_class: { type: "string", description: "父类 (默认 Actor，可选 Pawn 等)" }
      },
      required: ["name"]
    }
  },
  {
    name: "add_component_to_blueprint",
    description: "给指定蓝图添加组件（如 StaticMeshComponent/PointLightComponent/SpotLightComponent 等）",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        component_type: { type: "string", description: "组件类型名（如 StaticMeshComponent）" },
        component_name: { type: "string", description: "组件变量名（唯一）" },
        location: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } },
        rotation: { type: "object", properties: { pitch: { type: "number" }, yaw: { type: "number" }, roll: { type: "number" } } },
        scale: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } }
      },
      required: ["blueprint_name", "component_type", "component_name"]
    }
  },
  {
    name: "set_component_property",
    description: "设置蓝图中组件的属性（位置、材质参数、灯光参数等）",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        component_name: { type: "string" },
        property_name: { type: "string", description: "属性名" },
        property_value: { type: "object", description: "属性值（支持数字、布尔、字符串、数组）" }
      },
      required: ["blueprint_name", "component_name", "property_name", "property_value"]
    }
  },
  {
    name: "set_static_mesh_properties",
    description: "设置蓝图中 StaticMeshComponent 的 Mesh / Material",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        component_name: { type: "string" },
        static_mesh: { type: "string", description: "静态网格资源路径（如 /Engine/BasicShapes/Cube.Cube）" },
        material: { type: "string", description: "材质资源路径（可选）" }
      },
      required: ["blueprint_name", "component_name", "static_mesh"]
    }
  },
  {
    name: "set_physics_properties",
    description: "设置组件的物理属性",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        component_name: { type: "string" },
        simulate_physics: { type: "boolean" },
        mass: { type: "number" },
        linear_damping: { type: "number" },
        angular_damping: { type: "number" }
      },
      required: ["blueprint_name", "component_name"]
    }
  },
  {
    name: "set_blueprint_property",
    description: "设置蓝图级别的属性",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        property_name: { type: "string" },
        property_value: { type: "object" }
      },
      required: ["blueprint_name", "property_name", "property_value"]
    }
  },
  {
    name: "compile_blueprint",
    description: "编译蓝图",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" }
      },
      required: ["blueprint_name"]
    }
  },
  {
    name: "spawn_blueprint_actor",
    description: "在关卡中生成蓝图 Actor（蓝图必须位于 /Game/Blueprints）",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        actor_name: { type: "string" },
        location: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } },
        rotation: { type: "object", properties: { pitch: { type: "number" }, yaw: { type: "number" }, roll: { type: "number" } } },
        scale: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } }
      },
      required: ["blueprint_name", "actor_name"]
    }
  },
  {
    name: "set_pawn_properties",
    description: "设置 Pawn 蓝图属性（自动控制、旋转等）",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        auto_possess_player: { type: "string", description: "自动控制方式 (Disabled/Player0/PlacedInWorld/etc)" },
        use_controller_rotation_yaw: { type: "boolean" },
        use_controller_rotation_pitch: { type: "boolean" },
        use_controller_rotation_roll: { type: "boolean" }
      },
      required: ["blueprint_name"]
    }
  },
  {
    name: "create_box",
    description: "直接在关卡中创建一个立方体（通过创建/复用蓝图 + 生成蓝图 Actor）",
    inputSchema: {
      type: "object",
      properties: {
        actor_name: { type: "string", description: "生成到场景里的 Actor 名称（可选）" },
        location: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } },
        rotation: { type: "object", properties: { pitch: { type: "number" }, yaw: { type: "number" }, roll: { type: "number" } } },
        scale: { type: "object", properties: { x: { type: "number" }, y: { type: "number" }, z: { type: "number" } } }
      }
    }
  },

  // ===== 蓝图节点编辑 =====
  {
    name: "add_blueprint_event_node",
    description: "在蓝图事件图中添加事件节点（如 EventTick, ReceiveBeginPlay, ReceiveEndPlay）",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        event_name: { type: "string", description: "事件名称 (Tick/ReceiveBeginPlay/ReceiveEndPlay/ActorBeginOverlap 等)" },
        node_position: { type: "object", properties: { x: { type: "number" }, y: { type: "number" } }, description: "节点位置（可选）" }
      },
      required: ["blueprint_name", "event_name"]
    }
  },
  {
    name: "add_blueprint_function_node",
    description: "在蓝图中添加一个函数调用节点，支持设置参数",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        function_name: { type: "string" },
        target: { type: "string", description: "目标类名 (如 KismetSystemLibrary, GameplayStatics)" },
        params: { type: "object", description: "参数字典 {key: value}" },
        node_position: { type: "object", properties: { x: { type: "number" }, y: { type: "number" } } }
      },
      required: ["blueprint_name", "function_name"]
    }
  },
  {
    name: "add_blueprint_variable",
    description: "在蓝图中添加变量",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        variable_name: { type: "string" },
        variable_type: { type: "string", description: "变量类型 (Boolean/Integer/Float/String/Vector)" },
        is_exposed: { type: "boolean", description: "是否在编辑器中暴露" }
      },
      required: ["blueprint_name", "variable_name", "variable_type"]
    }
  },
  {
    name: "add_blueprint_get_self_component_reference",
    description: "添加获取自身组件引用的节点",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        component_name: { type: "string", description: "组件变量名" },
        node_position: { type: "object", properties: { x: { type: "number" }, y: { type: "number" } } }
      },
      required: ["blueprint_name", "component_name"]
    }
  },
  {
    name: "connect_blueprint_nodes",
    description: "连接蓝图中的两个节点",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        source_node_id: { type: "string" },
        target_node_id: { type: "string" },
        source_pin: { type: "string" },
        target_pin: { type: "string" }
      },
      required: ["blueprint_name", "source_node_id", "target_node_id", "source_pin", "target_pin"]
    }
  },
  {
    name: "find_blueprint_nodes",
    description: "查找蓝图中的事件节点（返回节点 GUID）",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        node_type: { type: "string", description: "节点类型 (Event)" },
        event_name: { type: "string", description: "事件名（如 ReceiveBeginPlay/Tick）" }
      },
      required: ["blueprint_name", "node_type"]
    }
  },
  {
    name: "add_blueprint_self_reference",
    description: "添加 self 引用节点",
    inputSchema: {
      type: "object",
      properties: {
        blueprint_name: { type: "string" },
        node_position: { type: "object", properties: { x: { type: "number" }, y: { type: "number" } } }
      },
      required: ["blueprint_name"]
    }
  }
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

function createSocket() {
  const client = new net.Socket();
  client.setNoDelay(true);
  client.setTimeout(10000);
  return client;
}

function sendToUnreal(commandType, params) {
  return new Promise((resolve, reject) => {
    const client = createSocket();
    let buffer = '';
    let settled = false;

    const settleOnce = (fn, value) => {
      if (settled) return;
      settled = true;
      try { client.destroy(); } catch {}
      fn(value);
    };

    client.connect(UE_PORT, UE_HOST, () => {
      const payload = { type: commandType, params: params || {} };
      client.write(JSON.stringify(payload));
    });

    client.on('data', (data) => {
      buffer += data.toString('utf8');
      try {
        const json = JSON.parse(buffer);
        settleOnce(resolve, json);
      } catch {
      }
    });

    client.on('timeout', () => {
      settleOnce(reject, new Error(`连接虚幻引擎超时 (端口 ${UE_PORT})`));
    });

    client.on('error', (err) => {
      settleOnce(reject, err);
    });
  });
}

async function createBox(params) {
  const blueprintName = 'BP_MCP_Box';
  const componentName = 'BoxMesh';

  const createBlueprintResp = await sendToUnreal('create_blueprint', { name: blueprintName });
  if (createBlueprintResp && createBlueprintResp.status === 'error') {
    const msg = String(createBlueprintResp.error || '');
    if (!msg.toLowerCase().includes('already exists')) {
      throw new Error(msg || '创建蓝图失败');
    }
  }

  const addCompResp = await sendToUnreal('add_component_to_blueprint', {
    blueprint_name: blueprintName,
    component_type: 'StaticMeshComponent',
    component_name: componentName
  });
  if (addCompResp && addCompResp.status === 'error') {
    const msg = String(addCompResp.error || '');
    if (!msg.toLowerCase().includes('already exists') && !msg.toLowerCase().includes('component')) {
      throw new Error(msg || '添加组件失败');
    }
  }

  const meshResp = await sendToUnreal('set_static_mesh_properties', {
    blueprint_name: blueprintName,
    component_name: componentName,
    static_mesh: '/Engine/BasicShapes/Cube.Cube'
  });
  if (meshResp && meshResp.status === 'error') {
    throw new Error(String(meshResp.error || '设置静态网格失败'));
  }

  const compileResp = await sendToUnreal('compile_blueprint', { blueprint_name: blueprintName });
  if (compileResp && compileResp.status === 'error') {
    throw new Error(String(compileResp.error || '编译蓝图失败'));
  }

  const actorName = (params && params.actor_name) ? String(params.actor_name) : `MCP_Box_${Date.now()}`;
  const spawnParams = {
    blueprint_name: blueprintName,
    actor_name: actorName
  };
  if (params && params.location) spawnParams.location = params.location;
  if (params && params.rotation) spawnParams.rotation = params.rotation;
  if (params && params.scale) spawnParams.scale = params.scale;

  const spawnResp = await sendToUnreal('spawn_blueprint_actor', spawnParams);
  if (spawnResp && spawnResp.status === 'error') {
    throw new Error(String(spawnResp.error || '生成蓝图 Actor 失败'));
  }
  return spawnResp;
}

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    if (request.params.name === 'create_box') {
      const response = await createBox(request.params.arguments || {});
      return { content: [{ type: "text", text: JSON.stringify(response.result || response) }] };
    }

    const response = await sendToUnreal(request.params.name, request.params.arguments || {});
    return { content: [{ type: "text", text: JSON.stringify(response.result || response) }] };
  } catch (err) {
    return {
      isError: true,
      content: [{ type: "text", text: `MCP 调用失败: ${err && err.message ? err.message : String(err)}` }]
    };
  }
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Unreal MCP Bridge running...");
}

run().catch(console.error);
