# Geometry Nodes Hex Island Animation Notes

## Current Working Route

- The UE preview uses `GPU island motion`, not the experimental single-draw material WPO path.
- The target scene is `/Game/GN_Test_Scene`.
- The target actor is `ScifiHexSphere_OuterShell_GN`.
- Expected status after refresh:

```text
preview_animation_status: "GPU island motion: 30 islands for subdivision 2"
hex_subdivisions: 2
preview_islands: 30
vertices: 19656
triangles: 6552
```

## Important Lessons

- Do not treat every triangle face as an animation island. The island count must be derived from the Blender hex subdivision setting.
- For subdivision 2, the expected shell island count is 30, not hundreds of triangle-level objects.
- The smooth UE route is a transient `UBlenderGNFastDynamicMeshComponent` that groups indices by island and applies one render-batch transform per island.
- Avoid per-frame CPU vertex uploads for the breathing effect. They are easy to make correct visually, but too costly for this asset.
- Avoid the abandoned material WPO experiment unless it is redesigned and validated from scratch. The editor asset `M_GN_HexIsland_WPO` caused transparent/default-material confusion and was removed from the working route.
- `Force Default Material` must override fallback and material overrides for all procedural, fast dynamic, and island preview paths.
- When mesh data refreshes, destroy and rebuild the transient fast mesh so parameter changes are reflected immediately.
- Keep `DisplayName` and `SocketName` synchronized from the socket name, but do not blindly trust serialized defaults. If an old map saved every input as `Hex Subdivisions`, repair the known 5-slot Hex Sphere input set by index before syncing labels.
- Use `TitleProperty = "SocketName"` on the input array so Details panel rows show the actual Geometry Nodes socket instead of a stale/default struct label.
- Before closing or restarting the editor, always run `save_all`.

## Recommended MCP Verification

Use the direct TCP bridge on `127.0.0.1:55557`.

```js
await send("open_level", { path: "/Game/GN_Test_Scene" });
await send("focus_viewport", {
  target: "ScifiHexSphere_OuterShell_GN",
  distance: 650,
  realtime: true,
  orientation: { pitch: -5, yaw: 0, roll: 0 }
});
await send("openclaw_gn_get_status", {
  actor_name: "ScifiHexSphere_OuterShell_GN"
});
```

The status response should include these matching input labels:

```text
Hex Subdivisions
Tile Gap
Breath Amplitude
Breath Speed
Breath Noise Scale
```

Use `openclaw_gn_configure_refresh` with:

```json
{
  "actor_name": "ScifiHexSphere_OuterShell_GN",
  "force_default_material": true,
  "clear_fallback_material": true,
  "clear_material_overrides": true,
  "enable_preview_animation": true,
  "preview_animation_frame_rate": 60,
  "refresh_mode": "on_parameter_change",
  "minimum_refresh_interval": 0.08,
  "fixed_refresh_interval": 0.25
}
```

## Rollback Boundary

If the animation becomes invisible or the editor material turns translucent again, return to the GPU island motion path and remove any WPO material references from the actor before debugging deeper.
