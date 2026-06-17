import unreal


ASSET_DIR = "/Game/DistanceLerpMatrix"
MAP_PATH = f"{ASSET_DIR}/L_NonlinearDistanceLerpMatrix"
CURVE_NAME = "C_CustomLerp"
CYLINDER_MATERIAL_NAME = "M_MatrixCylinder_SoftWhite"
FLOOR_MATERIAL_NAME = "M_MatrixFloor_MagneticGreen"
TARGET_MATERIAL_NAME = "M_TargetSphere_PolishedSilver"
ARROW_MATERIAL_NAME = "M_DirectionArrow_DarkInk"
FIELD_BLUEPRINT_NAME = "BP_CylinderMatrixField"

MATRIX_COLUMNS = 11
MATRIX_ROWS = 11
MATRIX_SPACING = 130.0
MATRIX_RADIUS = 25.0
MATRIX_PLANE_HEIGHT = 12.0
MATRIX_REST_HEIGHT = 100.0
MATRIX_FALLOFF_RADIUS = 500.0


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def save_asset(asset):
    if asset:
        unreal.EditorAssetLibrary.save_loaded_asset(asset)


def create_material(asset_name, color, roughness=0.45, metallic=0.0):
    path = f"{ASSET_DIR}/{asset_name}"
    existing = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if existing:
        return existing

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    material = tools.create_asset(asset_name, ASSET_DIR, unreal.Material, factory)
    material.set_editor_property("use_material_attributes", False)

    base_color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant4Vector)
    base_color.set_editor_property("constant", color)
    unreal.MaterialEditingLibrary.connect_material_property(base_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    metal = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)

    unreal.MaterialEditingLibrary.recompile_material(material)
    save_asset(material)
    return material


def create_curve():
    curve_path = f"{ASSET_DIR}/{CURVE_NAME}"
    existing = unreal.EditorAssetLibrary.load_asset(curve_path) if unreal.EditorAssetLibrary.does_asset_exist(curve_path) else None
    if existing:
        return existing

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.CurveFactory()
    factory.set_editor_property("curve_class", unreal.CurveFloat)
    curve = tools.create_asset(CURVE_NAME, ASSET_DIR, unreal.CurveFloat, factory)
    # UE 5.7 keeps UCurveFloat.FloatCurve protected in Python. The C++ actor
    # uses the same smooth bell curve as a fallback when this editable asset has no keys.
    save_asset(curve)
    return curve


def create_field_blueprint():
    blueprint_path = f"{ASSET_DIR}/{FIELD_BLUEPRINT_NAME}"
    generated_class_path = f"{blueprint_path}.{FIELD_BLUEPRINT_NAME}_C"
    existing_class = unreal.load_class(None, generated_class_path)
    if existing_class:
        return existing_class

    field_class = unreal.load_class(None, "/Script/MCPGameProject.CylinderMatrixField")
    if not field_class:
        raise RuntimeError("Could not load /Script/MCPGameProject.CylinderMatrixField. Build the project before running this script.")

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", field_class)
    blueprint = tools.create_asset(FIELD_BLUEPRINT_NAME, ASSET_DIR, unreal.Blueprint, factory)
    save_asset(blueprint)

    generated_class = unreal.load_class(None, generated_class_path)
    if not generated_class:
        raise RuntimeError(f"Could not load generated class {generated_class_path}")
    return generated_class


def set_label(actor, label):
    try:
        actor.set_actor_label(label)
    except Exception:
        pass


def add_actor_tag(actor, tag):
    tags = list(actor.get_editor_property("tags"))
    unreal_tag = unreal.Name(tag)
    if unreal_tag not in tags:
        tags.append(unreal_tag)
        actor.set_editor_property("tags", tags)


def set_mesh(actor, mesh_path, material=None):
    component = actor.static_mesh_component if hasattr(actor, "static_mesh_component") else actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if component and mesh:
        component.set_static_mesh(mesh)
        if material:
            component.set_material(0, material)
    return component


def spawn_static_mesh(label, mesh_path, location, rotation=(0, 0, 0), scale=(1, 1, 1), material=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(*rotation),
    )
    set_label(actor, label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    set_mesh(actor, mesh_path, material)
    return actor


def find_component(actor, name):
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        if component.get_name() == name:
            return component
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        if component.get_name() == name:
            return component
    return None


def add_lighting():
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))
    set_label(sky, "Matrix_SkyLight")
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_component:
        sky_component.set_editor_property("intensity", 1.2)
        sky_component.set_editor_property("real_time_capture", True)

    key = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(-400, -500, 900), unreal.Rotator(-42, -35, 0))
    set_label(key, "Matrix_KeyLight")
    key_component = key.get_component_by_class(unreal.DirectionalLightComponent)
    if key_component:
        key_component.set_editor_property("intensity", 4.0)
        key_component.set_editor_property("light_color", unreal.Color(255, 219, 184, 255))

    fill = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, unreal.Vector(500, 400, 520), unreal.Rotator(0, 0, 0))
    set_label(fill, "Matrix_FillLight")
    fill_component = fill.get_component_by_class(unreal.PointLightComponent)
    if fill_component:
        fill_component.set_editor_property("intensity", 8500.0)
        fill_component.set_editor_property("attenuation_radius", 1600.0)
        fill_component.set_editor_property("light_color", unreal.Color(173, 199, 255, 255))

    try:
        atmosphere = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        set_label(atmosphere, "Matrix_SkyAtmosphere")
    except Exception:
        pass


def add_camera():
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() == "Matrix_OverviewCamera":
                add_actor_tag(actor, "Matrix_OverviewCamera")
                return actor
        except Exception:
            pass

    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(-1450, -1450, 1050),
        unreal.Rotator(-35, 45, 0),
    )
    set_label(camera, "Matrix_OverviewCamera")
    add_actor_tag(camera, "Matrix_OverviewCamera")
    camera.camera_component.set_editor_property("field_of_view", 38.0)
    return camera


def add_runtime_camera_lock(camera):
    lock_class = unreal.load_class(None, "/Script/MCPGameProject.MatrixRuntimeCameraLock")
    if not lock_class:
        raise RuntimeError("Could not load /Script/MCPGameProject.MatrixRuntimeCameraLock. Build the project before running this script.")

    lock = unreal.EditorLevelLibrary.spawn_actor_from_class(lock_class, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    set_label(lock, "Matrix_RuntimeCameraLock")
    lock.set_editor_property("CameraActor", camera)
    lock.set_editor_property("CameraTag", unreal.Name("Matrix_OverviewCamera"))
    lock.set_editor_property("BlendTime", 0.0)
    lock.set_editor_property("bReapplyEveryTick", True)
    return lock


def add_annotation():
    text = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(-920, 960, 80),
        unreal.Rotator(0, 135, 0),
    )
    set_label(text, "Matrix_TutorialNote")
    text_component = text.get_component_by_class(unreal.TextRenderComponent)
    if text_component:
        text_component.set_text("Xbox left stick moves the target sphere\\nWASD / arrow keys also work in Play mode")
        text_component.set_editor_property("world_size", 42.0)
        text_component.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_LEFT)
    return text


def cleanup_generated_actors():
    generated_labels = {
        "Matrix_Floor",
        "Matrix_TargetSphere_XboxPawn",
        "Matrix_DynamicCylinderField",
        "Matrix_SkyLight",
        "Matrix_KeyLight",
        "Matrix_FillLight",
        "Matrix_SkyAtmosphere",
        "Matrix_TutorialNote",
        "Matrix_RuntimeCameraLock",
    }
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() in generated_labels:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass


def create_level():
    ensure_directory(ASSET_DIR)

    curve = create_curve()
    cylinder_material = create_material(CYLINDER_MATERIAL_NAME, unreal.LinearColor(0.82, 0.88, 0.80, 1.0), 0.52, 0.0)
    floor_material = create_material(FLOOR_MATERIAL_NAME, unreal.LinearColor(0.16, 0.82, 0.08, 1.0), 0.58, 0.0)
    target_material = create_material(TARGET_MATERIAL_NAME, unreal.LinearColor(0.78, 0.76, 0.72, 1.0), 0.18, 0.75)
    arrow_material = create_material(ARROW_MATERIAL_NAME, unreal.LinearColor(0.08, 0.09, 0.11, 1.0), 0.5, 0.0)
    field_blueprint_class = create_field_blueprint()

    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        cleanup_generated_actors()
    else:
        world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if not world:
        raise RuntimeError(f"Failed to create level at {MAP_PATH}")

    floor = spawn_static_mesh(
        "Matrix_Floor",
        "/Engine/BasicShapes/Cube.Cube",
        (0, 0, -4),
        scale=(18, 18, 0.08),
        material=floor_material,
    )
    floor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)

    target_class = unreal.load_class(None, "/Script/MCPGameProject.MatrixTargetSpherePawn")
    if not target_class:
        raise RuntimeError("Could not load /Script/MCPGameProject.MatrixTargetSpherePawn. Build the project before running this script.")

    target = unreal.EditorLevelLibrary.spawn_actor_from_class(
        target_class,
        unreal.Vector(0, 0, 44),
        unreal.Rotator(0, 0, 0),
    )
    set_label(target, "Matrix_TargetSphere_XboxPawn")
    add_actor_tag(target, "Matrix_TargetSphere")
    target.set_actor_scale3d(unreal.Vector(0.85, 0.85, 0.85))
    target.set_editor_property("MoveSpeed", 650.0)
    target.set_editor_property("bNotifyMatrixFieldsOnMove", True)
    half_x = ((MATRIX_COLUMNS - 1) * MATRIX_SPACING * 0.5) - 40.0
    half_y = ((MATRIX_ROWS - 1) * MATRIX_SPACING * 0.5) - 40.0
    target.set_editor_property("MovementBoundsMin", unreal.Vector2D(-half_x, -half_y))
    target.set_editor_property("MovementBoundsMax", unreal.Vector2D(half_x, half_y))
    target_component = find_component(target, "Sphere")
    if target_component:
        target_component.set_material(0, target_material)
        target_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

    field = unreal.EditorLevelLibrary.spawn_actor_from_class(field_blueprint_class, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    set_label(field, "Matrix_DynamicCylinderField")
    field.set_editor_property("TargetActor", target)
    field.set_editor_property("TargetTag", unreal.Name("Matrix_TargetSphere"))
    field.set_editor_property("bAutoFindTargetActor", True)
    field.set_editor_property("FalloffCurve", curve)
    field.set_editor_property("Columns", MATRIX_COLUMNS)
    field.set_editor_property("Rows", MATRIX_ROWS)
    field.set_editor_property("Spacing", MATRIX_SPACING)
    field.set_editor_property("CylinderRadius", MATRIX_RADIUS)
    field.set_editor_property("PlaneHeight", MATRIX_PLANE_HEIGHT)
    field.set_editor_property("RestHeight", MATRIX_REST_HEIGHT)
    field.set_editor_property("FalloffRadius", MATRIX_FALLOFF_RADIUS)
    field.set_editor_property("HeightInterpSpeed", 8.0)
    field.set_editor_property("RuntimeUpdateInterval", 0.016)
    field.set_editor_property("bApplyBoundsToTarget", True)
    field.set_editor_property("TargetBoundsPadding", 40.0)
    field.rebuild_matrix()

    cylinder_component = find_component(field, "CylinderInstances")
    if cylinder_component:
        cylinder_component.set_material(0, cylinder_material)
        cylinder_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    shaft_component = find_component(field, "DirectionShaftInstances")
    head_component = find_component(field, "DirectionHeadInstances")
    for marker_component in [shaft_component, head_component]:
        if marker_component:
            marker_component.set_material(0, arrow_material)
            marker_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

    add_lighting()
    camera = add_camera()
    add_runtime_camera_lock(camera)

    game_mode_class = unreal.load_class(None, f"{ASSET_DIR}/DistanceLerpMatrixGameMode.DistanceLerpMatrixGameMode_C")
    if game_mode_class:
        try:
            world.get_world_settings().set_editor_property("default_game_mode", game_mode_class)
        except Exception as exc:
            unreal.log_warning(f"Could not assign DistanceLerpMatrixGameMode as world override: {exc}")

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH):
        raise RuntimeError(f"Failed to save current level at {MAP_PATH}")
    unreal.log(f"Created nonlinear distance lerp matrix level at {MAP_PATH}")


if __name__ == "__main__":
    create_level()
