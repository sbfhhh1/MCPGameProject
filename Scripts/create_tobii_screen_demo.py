import unreal


ASSET_DIR = "/Game/TobiiEyeTracker5/Examples"
MAP_PATH = f"{ASSET_DIR}/ScreenBasedPrefabDemo"


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def save(asset):
    if asset:
        unreal.EditorAssetLibrary.save_loaded_asset(asset)


def material(name, color, metallic=0.0, roughness=0.45):
    path = f"{ASSET_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant4Vector)
    base.set_editor_property("constant", color)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    metal = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    save(mat)
    return mat


def spawn_mesh(label, mesh_path, location, scale, mat):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.static_mesh_component
    component.set_static_mesh(unreal.EditorAssetLibrary.load_asset(mesh_path))
    component.set_material(0, mat)
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    return actor


def create_level():
    ensure_dir(ASSET_DIR)
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if not world:
        raise RuntimeError("Could not create Tobii demo map")

    target_mat = material("M_TobiiTarget", unreal.LinearColor(0.12, 0.55, 0.95, 1.0), 0.35, 0.22)
    accent_mat = material("M_TobiiAccent", unreal.LinearColor(0.95, 0.24, 0.08, 1.0), 0.1, 0.28)
    floor_mat = material("M_TobiiFloor", unreal.LinearColor(0.025, 0.045, 0.08, 1.0), 0.15, 0.62)

    floor = spawn_mesh("Tobii_Floor", "/Engine/BasicShapes/Cube.Cube", (0, 400, -70), (14, 14, 0.1), floor_mat)
    left = spawn_mesh("CubeLeft", "/Engine/BasicShapes/Cube.Cube", (350, -320, 170), (1.25, 1.25, 1.25), target_mat)
    middle = spawn_mesh("CubeMiddle", "/Engine/BasicShapes/Cube.Cube", (650, 0, 170), (1.25, 1.25, 1.25), target_mat)
    right = spawn_mesh("CubeRight", "/Engine/BasicShapes/Cube.Cube", (350, 320, 170), (1.25, 1.25, 1.25), target_mat)
    spawn_mesh("Sphere", "/Engine/BasicShapes/Sphere.Sphere", (650, -430, 80), (0.85, 0.85, 0.85), accent_mat)
    spawn_mesh("Capsule", "/Engine/BasicShapes/Cylinder.Cylinder", (650, 430, 120), (0.75, 0.75, 1.1), accent_mat)

    key = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 800), unreal.Rotator(-35, -20, 25))
    key.set_actor_label("Tobii_KeyLight")
    key.light_component.set_editor_property("intensity", 5.0)
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 600), unreal.Rotator())
    sky.set_actor_label("Tobii_SkyLight")
    sky.light_component.set_editor_property("intensity", 1.5)

    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-650, 0, 250), unreal.Rotator(0, 0, 0))
    camera.set_actor_label("Tobii_FixedCamera")
    camera.camera_component.set_editor_property("field_of_view", 60.0)

    lock_class = unreal.load_class(None, "/Script/MCPGameProject.MatrixRuntimeCameraLock")
    if lock_class:
        lock = unreal.EditorLevelLibrary.spawn_actor_from_class(lock_class, unreal.Vector(), unreal.Rotator())
        lock.set_actor_label("Tobii_CameraLock")
        lock.set_editor_property("camera_actor", camera)
        lock.set_editor_property("blend_time", 0.0)
        lock.set_editor_property("bReapplyEveryTick", True)

    demo_class = unreal.load_class(None, "/Script/TobiiEyeTracker5.TobiiScreenBasedDemoActor")
    if not demo_class:
        raise RuntimeError("Build and load TobiiEyeTracker5 plugin before generating the map")
    demo = unreal.EditorLevelLibrary.spawn_actor_from_class(demo_class, unreal.Vector(), unreal.Rotator())
    demo.set_actor_label("Tobii_ScreenBasedPrefabDemo")
    demo.set_editor_property("gaze_targets", [left, middle, right])
    demo.set_editor_property("bEnableSimulationAtStart", False)

    note = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(100, -600, 420), unreal.Rotator(0, 0, 0))
    note.set_actor_label("Tobii_Instructions")
    note.text_render.set_text("Look at left / middle / right cube\\nC Calibration  T Guide  S Record  F8 Simulation")
    note.text_render.set_editor_property("world_size", 34.0)
    note.text_render.set_editor_property("text_render_color", unreal.Color(120, 230, 255, 255))

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH):
        raise RuntimeError(f"Could not save {MAP_PATH}")
    unreal.log(f"Created Tobii Eye Tracker 5 demo map: {MAP_PATH}")


create_level()
