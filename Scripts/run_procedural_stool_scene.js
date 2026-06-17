const net = require('net');

function send(type, params = {}) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    let buffer = '';
    client.setNoDelay(true);
    client.setTimeout(60000);

    client.connect(55557, '127.0.0.1', () => {
      client.write(JSON.stringify({ type, params }));
    });

    client.on('data', (data) => {
      buffer += data.toString('utf8');
      try {
        const json = JSON.parse(buffer);
        client.destroy();
        resolve(json);
      } catch {}
    });

    client.on('timeout', () => {
      client.destroy();
      reject(new Error(`timeout: ${type}`));
    });
    client.on('error', reject);
  });
}

const stoolInputs = [
  ['Seat Radius', 'float', 0.445, 0.32, 0.62],
  ['Seat Thickness', 'float', 0.082, 0.045, 0.16],
  ['Leg Height', 'float', 1.05, 0.78, 1.32],
  ['Leg Radius', 'float', 0.022, 0.012, 0.045],
  ['Leg Spread', 'float', 0.355, 0.24, 0.52],
  ['Leg Segments', 'int', 28, 12, 48],
  ['Brace Height', 'float', 0.42, 0.24, 0.66],
  ['Foot Pad Scale', 'float', 0.62, 0.25, 1.0],
].map(([name, type, value, slider_min, slider_max]) => ({
  name,
  display_name: name,
  socket_name: name,
  fallback_identifier: name,
  type,
  value,
  slider_min,
  slider_max,
}));

async function main() {
  await send('open_level', { level_path: '/Game/Stool/Stool_demo' }).catch(() => null);

  const currentActors = await send('get_actors_in_level', {}).catch(() => null);
  const actors = currentActors?.result?.actors || [];
  for (const actor of actors) {
    if (actor.class === 'BlenderGeometryNodesActor' || actor.class === 'StoolRuntimePanelHost') {
      await send('delete_actor', { name: actor.name }).catch(() => null);
    }
  }

  for (const name of [
    'Procedural_Stool_Runtime',
    'Stool_DiamondMarbleActor',
    'Stool_Actor',
    'Procedural_Stool_Camera',
    'Procedural_Stool_KeyLight',
    'Procedural_Stool_FillLight',
    'Procedural_Stool_SkyLight',
    'Procedural_Stool_CameraLock',
    'Procedural_Stool_RuntimePanelHost',
  ]) {
    await send('delete_actor', { name }).catch(() => null);
  }

  const stool = await send('spawn_actor', {
    type: '/Script/OpenClawBlenderGeometryNodes.BlenderGeometryNodesActor',
    name: 'Procedural_Stool_Runtime',
    location: [0, 0, 8],
    rotation: [0, 0, 0],
    scale: [1, 1, 1],
  });
  console.log(JSON.stringify(stool, null, 2));

  const configured = await send('openclaw_gn_configure_refresh', {
    actor_name: 'Procedural_Stool_Runtime',
    blender_executable: 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe',
    blend_file: 'C:/UE_Project/MCPGameProject/Content/Stool/Stool.blend',
    object_name: 'Procedural_Stool',
    modifier_name: 'Procedural_Stool_GN',
    sidecar_script: 'C:/UE_Project/MCPGameProject/Plugins/OpenClawBlenderGeometryNodes/Content/Python/unreal_gn_eval.py',
    refresh_mode: 'manual',
    timeout_seconds: 60,
    minimum_refresh_interval: 0.12,
    use_binary_mesh_cache: true,
    apply_imported_normals: true,
    smooth_normals_by_position: false,
    enable_preview_animation: false,
    cast_shadows: true,
    inputs: stoolInputs,
  });
  console.log(JSON.stringify(configured, null, 2));

  await send('spawn_actor', {
    type: 'CameraActor',
    name: 'Procedural_Stool_Camera',
    location: [-420, 520, 260],
    rotation: [-21, -51, 0],
    scale: [1, 1, 1],
  });

  await send('spawn_actor', {
    type: 'DirectionalLight',
    name: 'Procedural_Stool_KeyLight',
    location: [-250, 350, 650],
    rotation: [-38, -32, 0],
    scale: [1, 1, 1],
  });

  await send('spawn_actor', {
    type: 'PointLight',
    name: 'Procedural_Stool_FillLight',
    location: [280, -260, 260],
    rotation: [0, 0, 0],
    scale: [1, 1, 1],
  });

  await send('spawn_actor', {
    type: '/Script/MCPGameProject.StoolRuntimePanelHost',
    name: 'Procedural_Stool_RuntimePanelHost',
    location: [0, 0, 0],
    rotation: [0, 0, 0],
    scale: [1, 1, 1],
  });

  await send('focus_viewport', {
    location: [0, 0, 80],
    distance: 520,
    orientation: [-18, -42, 0],
    realtime: true,
  });

  let status;
  for (let i = 0; i < 90; i += 1) {
    status = await send('openclaw_gn_get_status', { actor_name: 'Procedural_Stool_Runtime' });
    const result = status.result || {};
    if (!result.is_running && result.vertices > 0 && result.triangles > 0) break;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  console.log(JSON.stringify(status, null, 2));

  await send('openclaw_gn_dump_mesh_debug', {
    actor_name: 'Procedural_Stool_Runtime',
    output_path: 'C:/UE_Project/MCPGameProject/Saved/StoolVerify/stool_gn_mesh_debug.json',
  }).then((r) => console.log(JSON.stringify(r, null, 2))).catch(() => null);

  await send('save_all', {});
  console.log('OpenClaw procedural stool scene ready.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
