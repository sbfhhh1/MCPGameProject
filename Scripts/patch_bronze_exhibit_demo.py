import os
import unreal


MAP_PATH = "/Game/TobiiEyeTracker5/Examples/ScreenBasedPrefabDemo"
PROJECT_DIR = unreal.Paths.project_dir()
SOURCE_ART_DIR = os.path.join(PROJECT_DIR, "Content", "BronzeExhibit", "SourceArt")
VISUAL_DIR = "/Game/BronzeExhibit/Visual"
FONT_DIR = "/Game/BronzeExhibit/Fonts"
BRONZE_TAG_PREFIX = "BronzeExhibit."
PRESERVE_TAG_PREFIX = "BronzeExhibit.Preserve."
KEY_CONTEXT_CLASSES = {
    "SkyAtmosphere",
    "VolumetricCloud",
    "ExponentialHeightFog",
}
LEGACY_GEOMETRY_LABELS = {
    "Tobii_Floor",
    "CubeLeft",
    "CubeMiddle",
    "CubeRight",
    "Sphere",
    "Capsule",
}


def log(message):
    unreal.log(f"[BronzeExhibitPatch] {message}")


def import_source_asset(source_path, destination_path, destination_name):
    asset_path = f"{destination_path}/{destination_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    if not os.path.isfile(source_path):
        log(f"Optional source asset missing: {source_path}")
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source_path)
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("destination_name", destination_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.EditorAssetLibrary.load_asset(asset_path)


def import_visual_assets():
    background = import_source_asset(
        os.path.join(SOURCE_ART_DIR, "T_Bronze_InkMountains_Source.png"),
        VISUAL_DIR,
        "T_Bronze_InkMountains",
    )
    ornaments = import_source_asset(
        os.path.join(SOURCE_ART_DIR, "T_Bronze_Ornaments_Source.png"),
        VISUAL_DIR,
        "T_Bronze_Ornaments",
    )
    font = import_source_asset(
        os.path.join(SOURCE_ART_DIR, "NotoSerifSC-VF.ttf"),
        FONT_DIR,
        "NotoSerifSC",
    )
    log(
        "Imported optional presentation assets: "
        f"background={bool(background)}, ornaments={bool(ornaments)}, font={bool(font)}"
    )


def get_all_actors():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if subsystem:
        return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def spawn_actor(actor_class, location, rotation):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if subsystem:
        return subsystem.spawn_actor_from_class(actor_class, location, rotation)
    return unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)


def has_tag(actor, tag):
    return any(str(existing) == tag for existing in actor.tags)


def add_tags(actor, *tags):
    values = [unreal.Name(str(existing)) for existing in actor.tags]
    existing = {str(value) for value in values}
    for tag in tags:
        if tag not in existing:
            values.append(unreal.Name(tag))
    actor.set_editor_property("tags", values)


def find_managed_actor(tag, label):
    for actor in get_all_actors():
        if has_tag(actor, tag) or actor.get_actor_label() == label:
            return actor
    return None


def ensure_actor(actor_class, tag_suffix, label, location, rotation=unreal.Rotator()):
    tag = f"{BRONZE_TAG_PREFIX}{tag_suffix}"
    expected_class = actor_class.static_class() if isinstance(actor_class, type) else actor_class
    actor = find_managed_actor(tag, label)
    if actor and actor.get_class() != expected_class:
        raise RuntimeError(
            f"{label} exists as {actor.get_class().get_name()}, expected {expected_class.get_name()}"
        )
    if not actor:
        actor = spawn_actor(expected_class, location, rotation)
        if not actor:
            raise RuntimeError(f"Could not spawn {label}")
        log(f"Spawned {label}")
    actor.modify()
    actor.set_actor_label(label)
    add_tags(actor, tag)
    actor.set_actor_location_and_rotation(location, rotation, False, False)
    actor.set_actor_hidden_in_game(False)
    actor.set_actor_tick_enabled(True)
    return actor


def set_component_visibility(component, visible):
    if not component:
        return
    component.modify()
    component.set_editor_property("visible", visible)
    component.set_editor_property("hidden_in_game", not visible)


def hide_actor(actor, disable_tick=False):
    actor.modify()
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    if disable_tick:
        actor.set_actor_tick_enabled(False)
    for component in actor.get_components_by_class(unreal.SceneComponent):
        set_component_visibility(component, False)


def ensure_mesh(tag_suffix, label, mesh_path, location, scale, rotation=unreal.Rotator()):
    actor = ensure_actor(unreal.StaticMeshActor, tag_suffix, label, location, rotation)
    actor.set_actor_scale3d(scale)
    component = actor.static_mesh_component
    component.modify()
    component.set_static_mesh(unreal.EditorAssetLibrary.load_asset(mesh_path))
    component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    set_component_visibility(component, True)
    return actor


def ensure_point_light(tag_suffix, label, location, color, intensity, radius):
    actor = ensure_actor(unreal.PointLight, tag_suffix, label, location)
    component = actor.point_light_component
    component.modify()
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", radius)
    component.set_editor_property("light_color", color)
    set_component_visibility(component, True)
    return actor


def record_context_actor_names(host, actors):
    preserved = []
    for actor in actors:
        if actor.get_class().get_name() in KEY_CONTEXT_CLASSES:
            preserved.append(actor.get_name())
    if not preserved:
        raise RuntimeError("No key pre-existing environment actors found to preserve")
    add_tags(host, *[f"{PRESERVE_TAG_PREFIX}{name}" for name in sorted(preserved)])
    log(f"Recorded key context actors: {sorted(preserved)}")


def hide_legacy_demo(actors):
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors:
        label = actor.get_actor_label()
        class_name = actor.get_class().get_name()
        if label in LEGACY_GEOMETRY_LABELS or isinstance(actor, unreal.TextRenderActor):
            hide_actor(actor)
            log(f"Hidden legacy visual: {label}")
        if class_name == "TobiiScreenBasedDemoActor":
            if not actor_subsystem or not actor_subsystem.destroy_actor(actor):
                raise RuntimeError(f"Could not remove known legacy Tobii demo actor: {label}")
            log(f"Removed known legacy Tobii demo actor: {label}")
        elif "hud" in label.lower() or "hud" in class_name.lower():
            hide_actor(actor, disable_tick=True)
            log(f"Disabled legacy demo/HUD actor: {label}")


def save_current_level():
    subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if subsystem:
        return subsystem.save_current_level()
    return unreal.EditorLevelLibrary.save_current_level()


def patch_level():
    import_visual_assets()
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError(f"Could not load existing map {MAP_PATH}")

    host_class = unreal.load_class(None, "/Script/MCPGameProject.BronzeExhibitHost")
    stage_class = unreal.load_class(None, "/Script/MCPGameProject.BronzeArtifactStage")
    widget_class = unreal.load_class(None, "/Script/MCPGameProject.BronzeExhibitWidget")
    if not host_class or not stage_class or not widget_class:
        raise RuntimeError("Build and load the MCPGameProject Bronze Exhibit classes before running this script")

    actors_before = get_all_actors()
    hide_legacy_demo(actors_before)

    host = ensure_actor(
        host_class,
        "Host",
        "Bronze Exhibit Host",
        unreal.Vector(0.0, 0.0, 0.0),
    )
    record_context_actor_names(host, actors_before)

    stage = ensure_actor(
        stage_class,
        "ArtifactStage",
        "Bronze Exhibit ArtifactStage",
        unreal.Vector(520.0, 0.0, 175.0),
    )
    add_tags(stage, "BronzeArtifactStage")
    artifact_component = stage.get_editor_property("artifact_mesh")
    artifact_component.modify()
    artifact_component.set_static_mesh(
        unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    )
    set_component_visibility(artifact_component, True)
    stage.set_editor_property("bRotationEnabled", True)

    host.set_editor_property("artifact_stage", stage)
    host.set_editor_property("artifact_stage_tag", unreal.Name("BronzeArtifactStage"))
    host.set_editor_property("bSpawnStageIfMissing", False)
    host.set_editor_property("widget_class", widget_class)
    host.set_editor_property("bAutoPlayAtStart", False)
    host.set_editor_property("bEnableTobiiSimulationAtStart", False)
    host_defaults = unreal.get_default_object(host_class)
    host.set_editor_property("chapters", host_defaults.get_editor_property("chapters"))
    log("Synchronized Host chapter data from the latest C++ class defaults")

    ensure_mesh(
        "StageBase",
        "Bronze Exhibit Stage Base",
        "/Engine/BasicShapes/Cylinder.Cylinder",
        unreal.Vector(520.0, 0.0, 45.0),
        unreal.Vector(2.8, 2.8, 0.45),
    )
    ensure_mesh(
        "Floor",
        "Bronze Exhibit Floor",
        "/Engine/BasicShapes/Cube.Cube",
        unreal.Vector(450.0, 0.0, -25.0),
        unreal.Vector(9.0, 9.0, 0.25),
    )
    ensure_mesh(
        "Backdrop",
        "Bronze Exhibit Backdrop",
        "/Engine/BasicShapes/Cube.Cube",
        unreal.Vector(900.0, 0.0, 350.0),
        unreal.Vector(0.25, 9.0, 4.0),
    )
    ensure_point_light(
        "KeyLight",
        "Bronze Exhibit Key Light",
        unreal.Vector(100.0, -350.0, 550.0),
        unreal.Color(255, 190, 120, 255),
        8500.0,
        1500.0,
    )
    ensure_point_light(
        "FillLight",
        "Bronze Exhibit Fill Light",
        unreal.Vector(200.0, 450.0, 320.0),
        unreal.Color(90, 135, 255, 255),
        4200.0,
        1300.0,
    )
    ensure_point_light(
        "RimLight",
        "Bronze Exhibit Rim Light",
        unreal.Vector(850.0, 0.0, 500.0),
        unreal.Color(255, 125, 55, 255),
        6000.0,
        1100.0,
    )

    if not save_current_level():
        raise RuntimeError(f"Could not save current level {MAP_PATH}")
    log(f"Patched and saved existing map {MAP_PATH}")


patch_level()
