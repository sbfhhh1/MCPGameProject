"""
create_stool_level.py
=====================
Creates the Stool Diamond-Marble Material runtime demo level.

Run from the UE5 Editor's Python console:
    import importlib, sys
    sys.path.insert(0, r"C:/UE_Project/MCPGameProject/Scripts")
    import create_stool_level
    importlib.reload(create_stool_level)
    create_stool_level.create_level()

What this script builds
-----------------------
Content/Stool/
    L_Stool_GN_Runtime.umap          ← new level
    M_StoolDiamondMarble.uasset      ← procedural material (7 scalar params)
    StoolGameMode.uasset             ← Blueprint GameMode (creates widget on BeginPlay)
    StoolPawn.uasset                 ← Blueprint Pawn (spectator camera)
"""

import unreal

ASSET_DIR  = "/Game/Stool"
MAP_PATH   = f"{ASSET_DIR}/L_Stool_GN_Runtime"
MAT_NAME   = "M_StoolDiamondMarble"
GM_NAME    = "StoolGameMode"
PAWN_NAME  = "StoolPawn"

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg):
    unreal.log(f"[StoolLevel] {msg}")

def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def save(asset):
    if asset:
        unreal.EditorAssetLibrary.save_loaded_asset(asset)

def load_or_none(path):
    return unreal.EditorAssetLibrary.load_asset(path) \
        if unreal.EditorAssetLibrary.does_asset_exist(path) else None

# ── Material creation ─────────────────────────────────────────────────────────

def make_scalar_param(mat, name, default_val, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", default_val)
    return node

def create_material():
    mat_path = f"{ASSET_DIR}/{MAT_NAME}"
    existing = load_or_none(mat_path)
    if existing:
        log(f"Material already exists: {mat_path}")
        return existing

    tools   = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    mat     = tools.create_asset(MAT_NAME, ASSET_DIR, unreal.Material, factory)
    if not mat:
        raise RuntimeError(f"Failed to create material at {mat_path}")

    mel = unreal.MaterialEditingLibrary

    # ── Scalar parameters ─────────────────────────────────────────────────────
    # (name, default, node-graph x, y)
    p_scale    = make_scalar_param(mat, "Scale",              1.0,  -1400, -600)
    p_rough    = make_scalar_param(mat, "Roughness",          0.1,  -1400, -500)
    p_marble   = make_scalar_param(mat, "Marble Scale",       7.0,  -1400, -400)
    p_diamond  = make_scalar_param(mat, "Diamond Scale",      1.0,  -1400, -300)
    p_tile_vis = make_scalar_param(mat, "Tile Visibility",    0.2,  -1400, -200)
    p_tile_bmp = make_scalar_param(mat, "Tile Bump Strength", 0.8,  -1400, -100)
    p_noise_bmp= make_scalar_param(mat, "Noise Bump Strength",0.1,  -1400,    0)

    # ── UV tiling: TexCoord × Scale ───────────────────────────────────────────
    tc = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1150, -560)
    mul_uv = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply,       -950, -560)
    mel.connect_material_expressions(tc,      "", mul_uv, "A")
    mel.connect_material_expressions(p_scale, "", mul_uv, "B")

    # ── Marble noise (UV × MarbleScale → Noise) ───────────────────────────────
    mul_marble = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -750, -460)
    mel.connect_material_expressions(mul_uv,   "", mul_marble, "A")
    mel.connect_material_expressions(p_marble, "", mul_marble, "B")

    noise_marble = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -560, -460)
    noise_marble.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX3D)
    noise_marble.set_editor_property("levels", 4)
    mel.connect_material_expressions(mul_marble, "", noise_marble, "Position")

    # Map noise [-1,1] → [0,1] for colour use
    add_half = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -370, -460)
    add_half.set_editor_property("const_b", 1.0)
    mel.connect_material_expressions(noise_marble, "", add_half, "A")

    mul_half = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, -460)
    mul_half.set_editor_property("const_b", 0.5)
    mel.connect_material_expressions(add_half, "", mul_half, "A")

    # Marble base colour: lerp white ↔ dark grey via noise
    white = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -220, -600)
    white.set_editor_property("constant", unreal.LinearColor(0.95, 0.95, 0.95, 1.0))

    dark_grey = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -220, -520)
    dark_grey.set_editor_property("constant", unreal.LinearColor(0.13, 0.13, 0.13, 1.0))

    lerp_marble = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -30, -540)
    mel.connect_material_expressions(white,    "", lerp_marble, "A")
    mel.connect_material_expressions(dark_grey,"", lerp_marble, "B")
    mel.connect_material_expressions(mul_half, "", lerp_marble, "Alpha")

    # ── Diamond Voronoi-style pattern (UV × DiamondScale → Noise faster) ─────
    mul_diamond = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -750, -260)
    mel.connect_material_expressions(mul_uv,    "", mul_diamond, "A")
    mel.connect_material_expressions(p_diamond, "", mul_diamond, "B")

    noise_diamond = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -560, -260)
    noise_diamond.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_VORONOI_ALU)
    noise_diamond.set_editor_property("levels", 1)
    mel.connect_material_expressions(mul_diamond, "", noise_diamond, "Position")

    # Diamond colour: lerp black ↔ gold
    gold = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -220, -300)
    gold.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))

    lerp_diamond = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -30, -340)
    mel.connect_material_expressions(dark_grey,    "", lerp_diamond, "A")
    mel.connect_material_expressions(gold,         "", lerp_diamond, "B")
    mel.connect_material_expressions(noise_diamond,"", lerp_diamond, "Alpha")

    # ── Blend marble & diamond via Tile Visibility ────────────────────────────
    lerp_blend = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 200, -460)
    mel.connect_material_expressions(lerp_marble,  "", lerp_blend, "A")
    mel.connect_material_expressions(lerp_diamond, "", lerp_blend, "B")
    mel.connect_material_expressions(p_tile_vis,   "", lerp_blend, "Alpha")

    # ── Connect BaseColor ─────────────────────────────────────────────────────
    mel.connect_material_property(lerp_blend, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # ── Roughness → Roughness output ──────────────────────────────────────────
    mel.connect_material_property(p_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    # ── Normal map from Tile Bump: scale noise_marble by TileBumpStrength ─────
    # (using marble noise gradient as a cheap bump approximation)
    mul_tile_bump = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, -140)
    mel.connect_material_expressions(noise_marble, "", mul_tile_bump, "A")
    mel.connect_material_expressions(p_tile_bmp,   "", mul_tile_bump, "B")

    # ── Noise bump: scale noise_diamond by NoiseBumpStrength ─────────────────
    mul_noise_bump = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, -60)
    mel.connect_material_expressions(noise_diamond, "", mul_noise_bump, "A")
    mel.connect_material_expressions(p_noise_bmp,   "", mul_noise_bump, "B")

    # Combine both bump contributions and feed to Pixel Depth Offset
    # (gives a subtle surface-displacement feel without a real normal map)
    add_bump = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -30, -100)
    mel.connect_material_expressions(mul_tile_bump,  "", add_bump, "A")
    mel.connect_material_expressions(mul_noise_bump, "", add_bump, "B")

    mel.connect_material_property(add_bump, "", unreal.MaterialProperty.MP_PIXEL_DEPTH_OFFSET)

    mel.recompile_material(mat)
    save(mat)
    log(f"Created material: {MAT_NAME}")
    return mat


# ── Blueprint GameMode (creates widget on BeginPlay) ─────────────────────────

def get_stool_game_mode_class():
    # Use the C++ AStoolGameMode (compiles with the project)
    gm_class = unreal.load_class(None, "/Script/MCPGameProject.StoolGameMode")
    if gm_class:
        log("Using C++ StoolGameMode")
        return gm_class

    # Fallback: Blueprint GameMode based on AStoolGameMode if available
    gm_path = f"{ASSET_DIR}/{GM_NAME}"
    existing_class = unreal.load_class(None, f"{gm_path}.{GM_NAME}_C")
    if existing_class:
        log(f"Using Blueprint GameMode: {gm_path}")
        return existing_class

    # Last resort: plain Blueprint GameModeBase
    tools   = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.GameModeBase)
    gm_bp   = tools.create_asset(GM_NAME, ASSET_DIR, unreal.Blueprint, factory)
    save(gm_bp)
    log(f"Created fallback Blueprint GameMode: {GM_NAME}")
    return unreal.load_class(None, f"{gm_path}.{GM_NAME}_C")


# ── Blueprint Pawn (spectator camera, no movement needed) ────────────────────

def create_pawn():
    pawn_path = f"{ASSET_DIR}/{PAWN_NAME}"
    existing_class = unreal.load_class(None, f"{pawn_path}.{PAWN_NAME}_C")
    if existing_class:
        log(f"Pawn already exists: {pawn_path}")
        return existing_class

    tools   = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Pawn)
    pawn_bp = tools.create_asset(PAWN_NAME, ASSET_DIR, unreal.Blueprint, factory)
    save(pawn_bp)
    log(f"Created Pawn Blueprint: {PAWN_NAME}")

    return unreal.load_class(None, f"{pawn_path}.{PAWN_NAME}_C")


# ── Level actors ──────────────────────────────────────────────────────────────

def cleanup(world, labels):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() in labels:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass


def add_lighting():
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))
    sky.set_actor_label("Stool_SkyLight")
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_comp:
        sky_comp.set_editor_property("intensity", 1.5)
        sky_comp.set_editor_property("real_time_capture", True)

    key = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(-300, -400, 800),
        unreal.Rotator(-45, -30, 0))
    key.set_actor_label("Stool_KeyLight")
    key_comp = key.get_component_by_class(unreal.DirectionalLightComponent)
    if key_comp:
        key_comp.set_editor_property("intensity", 5.0)
        key_comp.set_editor_property("light_color", unreal.Color(255, 230, 200, 255))

    fill = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(400, 300, 400),
        unreal.Rotator(0, 0, 0))
    fill.set_actor_label("Stool_FillLight")
    fill_comp = fill.get_component_by_class(unreal.PointLightComponent)
    if fill_comp:
        fill_comp.set_editor_property("intensity", 6000.0)
        fill_comp.set_editor_property("attenuation_radius", 1200.0)
        fill_comp.set_editor_property("light_color", unreal.Color(180, 210, 255, 255))

    try:
        atm = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        atm.set_actor_label("Stool_SkyAtmosphere")
    except Exception:
        pass


def add_camera():
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(-550, -550, 420),
        unreal.Rotator(-30, 45, 0))
    cam.set_actor_label("Stool_Camera")
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    if cam_comp:
        cam_comp.set_editor_property("field_of_view", 45.0)
    return cam


# ── Main entry point ──────────────────────────────────────────────────────────

def create_level():
    ensure_dir(ASSET_DIR)

    # 1. Material
    mat = create_material()

    # 2. GameMode class (C++ preferred) and Pawn Blueprint
    gm_class   = get_stool_game_mode_class()
    pawn_class = create_pawn()

    # 3. Load or create map
    cleanup_labels = {
        "Stool_SkyLight", "Stool_KeyLight", "Stool_FillLight",
        "Stool_SkyAtmosphere", "Stool_Camera",
        "Stool_Floor", "Stool_DiamondMarbleActor",
    }

    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        cleanup(world, cleanup_labels)
    else:
        world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)

    if not world:
        raise RuntimeError(f"Failed to open/create level at {MAP_PATH}")

    # 4. Spawn the StoolMaterialActor
    stool_class = unreal.load_class(None, "/Script/MCPGameProject.StoolMaterialActor")
    if not stool_class:
        raise RuntimeError(
            "Could not load /Script/MCPGameProject.StoolMaterialActor. "
            "Rebuild the C++ project first (compile StoolMaterialActor.h/.cpp)."
        )

    stool_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        stool_class,
        unreal.Vector(0, 0, 100),
        unreal.Rotator(0, 0, 0),
    )
    stool_actor.set_actor_label("Stool_DiamondMarbleActor")
    stool_actor.set_actor_scale3d(unreal.Vector(5.0, 5.0, 0.1))   # flat floor slab

    # Assign material
    stool_actor.set_editor_property("BaseMaterial", mat)

    # Set default parameter values to match Blender defaults
    stool_actor.set_editor_property("Scale",             1.0)
    stool_actor.set_editor_property("Roughness",         0.1)
    stool_actor.set_editor_property("MarbleScale",       7.0)
    stool_actor.set_editor_property("DiamondScale",      1.0)
    stool_actor.set_editor_property("TileVisibility",    0.2)
    stool_actor.set_editor_property("TileBumpStrength",  0.8)
    stool_actor.set_editor_property("NoiseBumpStrength", 0.1)

    # 5. Ground floor reference plane
    floor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(0, 0, 0),
        unreal.Rotator(0, 0, 0),
    )
    floor.set_actor_label("Stool_Floor")
    floor.set_actor_scale3d(unreal.Vector(20, 20, 0.05))
    mesh_obj = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    floor_mesh_comp = floor.get_component_by_class(unreal.StaticMeshComponent)
    if floor_mesh_comp and mesh_obj:
        floor_mesh_comp.set_static_mesh(mesh_obj)
        floor_mesh_comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)

    # 6. Lighting + Camera
    add_lighting()
    add_camera()

    # 7. World settings: GameMode
    ws = world.get_world_settings()
    if gm_class:
        try:
            ws.set_editor_property("default_game_mode", gm_class)
            log(f"Assigned GameMode: {GM_NAME}")
        except Exception as exc:
            unreal.log_warning(f"Could not assign GameMode: {exc}")

    # 8. Save
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH):
        raise RuntimeError(f"Failed to save level at {MAP_PATH}")

    log("=" * 60)
    log(f"Level saved: {MAP_PATH}")
    log("")
    log("NEXT STEPS:")
    log("  1. Rebuild the C++ project (Build → Build Solution in VS, or Live Coding).")
    log("  2. Open the level: Content/Stool/L_Stool_GN_Runtime")
    log("  3. Press Play – the StoolGameMode auto-creates the panel widget.")
    log("  4. Drag sliders to control Scale / Roughness / Marble Scale etc. in real time.")
    log("=" * 60)


if __name__ == "__main__":
    create_level()
