"""
setup_stool_scene.py
====================
Imports SM_Stool.fbx, rebuilds scene layout, and positions the camera
to match the Blender reference render.

Run from the UE5 Python console:
    import importlib, sys
    sys.path.insert(0, r"C:/UE_Project/MCPGameProject/Scripts")
    import setup_stool_scene; importlib.reload(setup_stool_scene)
    setup_stool_scene.setup()
"""

import unreal

ASSET_DIR  = "/Game/Stool"
MAP_PATH   = f"{ASSET_DIR}/L_Stool_GN_Runtime"
MESH_PATH  = f"{ASSET_DIR}/SM_Stool"
FBX_PATH   = r"C:/UE_Project/MCPGameProject/Content/Stool/SM_Stool.fbx"

def log(msg):
    unreal.log(f"[StoolScene] {msg}")

def destroy_by_label(labels):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() in labels:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass

def import_stool_mesh():
    """Import SM_Stool.fbx if the asset doesn't exist yet."""
    if unreal.EditorAssetLibrary.does_asset_exist(MESH_PATH):
        log("SM_Stool already imported, reusing existing asset.")
        return unreal.EditorAssetLibrary.load_asset(MESH_PATH)

    task = unreal.AssetImportTask()
    task.filename        = FBX_PATH
    task.destination_path = ASSET_DIR
    task.destination_name = "SM_Stool"
    task.replace_existing = True
    task.automated       = True
    task.save            = True

    opts = unreal.FbxImportUI()
    opts.import_mesh          = True
    opts.import_textures      = True
    opts.import_materials     = True
    opts.import_as_skeletal   = False
    opts.static_mesh_import_data.combine_meshes = True
    opts.static_mesh_import_data.generate_lightmap_u_vs = True
    opts.static_mesh_import_data.auto_generate_collision = True
    task.options = opts

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    if unreal.EditorAssetLibrary.does_asset_exist(MESH_PATH):
        log("SM_Stool imported successfully.")
        return unreal.EditorAssetLibrary.load_asset(MESH_PATH)
    else:
        raise RuntimeError(f"FBX import failed. Check path: {FBX_PATH}")


def setup():
    # 1. Import stool mesh
    stool_mesh = import_stool_mesh()

    # 2. Remove actors we will recreate
    destroy_by_label({
        "Stool_Camera", "Stool_KeyLight", "Stool_FillLight",
        "Stool_SkyLight", "Stool_SkyAtmosphere", "Stool_Floor",
        "Stool_DiamondMarbleActor", "Stool_Actor",
    })

    # ── 3. Diamond Marble floor slab (flat, flush with z=0) ────────────────────
    mat_path = f"{ASSET_DIR}/M_StoolDiamondMarble"
    mat = unreal.EditorAssetLibrary.load_asset(mat_path) if unreal.EditorAssetLibrary.does_asset_exist(mat_path) else None

    stool_class = unreal.load_class(None, "/Script/MCPGameProject.StoolMaterialActor")
    if stool_class:
        floor_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            stool_class, unreal.Vector(0, 0, -5), unreal.Rotator(0, 0, 0))
        floor_actor.set_actor_label("Stool_DiamondMarbleActor")
        # 600×600 cm floor, 10 cm thick, top surface at z=0
        floor_actor.set_actor_scale3d(unreal.Vector(6.0, 6.0, 0.1))
        if mat:
            floor_actor.set_editor_property("BaseMaterial", mat)
        log("Spawned DiamondMarble floor at z=-5 (top surface at z=0)")

    # ── 4. Stool mesh actor ────────────────────────────────────────────────────
    # Stool bottom sits at z=0; mesh origin is at its base in Blender
    stool_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    stool_actor.set_actor_label("Stool_Actor")
    mesh_comp = stool_actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp and stool_mesh:
        mesh_comp.set_static_mesh(stool_mesh)
        mesh_comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    log("Spawned stool mesh actor at origin")

    # ── 5. Lighting ─────────────────────────────────────────────────────────────
    # SkyLight
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))
    sky.set_actor_label("Stool_SkyLight")
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_comp:
        sky_comp.set_editor_property("intensity", 1.2)
        sky_comp.set_editor_property("real_time_capture", True)

    # Key light: front-left, 45° elevated – warm sun
    key = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0, 0, 800),
        unreal.Rotator(-45, -30, 0))
    key.set_actor_label("Stool_KeyLight")
    key_comp = key.get_component_by_class(unreal.DirectionalLightComponent)
    if key_comp:
        key_comp.set_editor_property("intensity", 6.0)
        key_comp.set_editor_property("light_color", unreal.Color(255, 235, 210, 255))
        key_comp.set_editor_property("cast_shadows", True)

    # Fill light: right/back, cool tone
    fill = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(300, 300, 300),
        unreal.Rotator(0, 0, 0))
    fill.set_actor_label("Stool_FillLight")
    fill_comp = fill.get_component_by_class(unreal.PointLightComponent)
    if fill_comp:
        fill_comp.set_editor_property("intensity", 5000.0)
        fill_comp.set_editor_property("attenuation_radius", 1500.0)
        fill_comp.set_editor_property("light_color", unreal.Color(180, 210, 255, 255))

    # Sky Atmosphere
    try:
        atm = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        atm.set_actor_label("Stool_SkyAtmosphere")
    except Exception:
        pass

    # ── 6. Camera – matches Blender reference angle ─────────────────────────────
    # Blender cam: pos (7.36, -6.93, 4.96)m, pitch≈-26.5°, yaw≈46.7°
    # UE5 (scaled ×100, axis mapping Blender→UE: X→Y, -Y→X, Z→Z):
    #   UE pos = (-693, 736, 496) → rounded to (-500, 550, 350) for tighter framing
    # Pitch -26° (looking slightly down), Yaw 48° (front-right quadrant)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(-500, 550, 350),
        unreal.Rotator(-26, 48, 0))
    cam.set_actor_label("Stool_Camera")
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    if cam_comp:
        cam_comp.set_editor_property("field_of_view", 40.0)
    log("Placed camera matching Blender reference angle")

    # ── 7. Save ─────────────────────────────────────────────────────────────────
    if unreal.EditorLoadingAndSavingUtils.save_map(
            unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH):
        log("Level saved: " + MAP_PATH)
    else:
        log("WARNING: save_map returned False – save manually if needed.")

    log("Done. Press Play to test the material control panel.")


if __name__ == "__main__":
    setup()
