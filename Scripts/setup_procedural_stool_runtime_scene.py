"""
Set up the current level as a procedural Stool.blend runtime demo.

This scene intentionally uses the existing OpenClaw Blender Geometry Nodes
plugin actor and runtime panel. No stool-specific Actor, GameMode, or widget
class is required.
"""

import unreal

STOOL_LABEL = "Procedural_Stool_Runtime"
CAMERA_LABEL = "Procedural_Stool_Camera"
KEY_LABEL = "Procedural_Stool_KeyLight"
FILL_LABEL = "Procedural_Stool_FillLight"
SKY_LABEL = "Procedural_Stool_SkyLight"
CAMERA_LOCK_LABEL = "Procedural_Stool_CameraLock"
PANEL_HOST_LABEL = "Procedural_Stool_RuntimePanelHost"

BLEND_FILE = r"C:/UE_Project/MCPGameProject/Content/Stool/Stool.blend"
SIDECAR = r"C:/UE_Project/MCPGameProject/Plugins/OpenClawBlenderGeometryNodes/Content/Python/unreal_gn_eval.py"
BLENDER_EXE = r"C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"


def log(message):
    unreal.log("[ProceduralStoolScene] " + message)


def destroy_by_label(labels):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() in labels:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass


def make_gn_input(name, input_type, value, slider_min, slider_max):
    entry = unreal.BlenderGNInput()
    entry.set_editor_property("DisplayName", name)
    entry.set_editor_property("SocketName", name)
    entry.set_editor_property("FallbackIdentifier", name)
    entry.set_editor_property("SliderMin", slider_min)
    entry.set_editor_property("SliderMax", slider_max)
    entry.set_editor_property("bShowInRuntimePanel", True)

    if input_type == "int":
        entry.set_editor_property("Type", unreal.BlenderGNParameterType.INT)
        entry.set_editor_property("IntValue", int(value))
    else:
        entry.set_editor_property("Type", unreal.BlenderGNParameterType.FLOAT)
        entry.set_editor_property("FloatValue", float(value))
    return entry


def configure_runtime(actor):
    runtime = actor.get_component_by_class(unreal.BlenderGeometryNodesComponent)
    if not runtime:
        raise RuntimeError("BlenderGeometryNodesActor has no BlenderGeometryNodesComponent")

    runtime.set_editor_property("BlenderExecutable", BLENDER_EXE)
    runtime.set_editor_property("BlendFile", unreal.FilePath(BLEND_FILE))
    runtime.set_editor_property("ObjectName", "Procedural_Stool")
    runtime.set_editor_property("ModifierName", "Procedural_Stool_GN")
    runtime.set_editor_property("SidecarScriptPath", SIDECAR)
    runtime.set_editor_property("RefreshMode", unreal.BlenderGNRefreshMode.MANUAL)
    runtime.set_editor_property("BlenderTimeoutSeconds", 60)
    runtime.set_editor_property("MinimumRefreshInterval", 0.12)
    runtime.set_editor_property("FixedRefreshInterval", 0.25)
    runtime.set_editor_property("bRefreshOnBeginPlay", True)
    runtime.set_editor_property("bUseBinaryMeshCache", True)
    runtime.set_editor_property("bApplyImportedNormals", True)
    runtime.set_editor_property("bSmoothNormalsByPosition", False)
    runtime.set_editor_property("bEnablePreviewAnimation", False)
    runtime.set_editor_property("bCastShadows", True)
    runtime.set_editor_property("BlenderToUnrealScale", 100.0)

    inputs = [
        make_gn_input("Seat Radius", "float", 0.445, 0.32, 0.62),
        make_gn_input("Seat Thickness", "float", 0.082, 0.045, 0.16),
        make_gn_input("Leg Height", "float", 1.05, 0.78, 1.32),
        make_gn_input("Leg Radius", "float", 0.022, 0.012, 0.045),
        make_gn_input("Leg Spread", "float", 0.355, 0.24, 0.52),
        make_gn_input("Leg Segments", "int", 28, 12.0, 48.0),
        make_gn_input("Brace Height", "float", 0.42, 0.24, 0.66),
        make_gn_input("Foot Pad Scale", "float", 0.62, 0.25, 1.0),
    ]
    runtime.set_editor_property("Inputs", inputs)

    materials = [
        unreal.load_asset("/Game/Stool/GN_Dark_Grey_Rubber_002"),
        unreal.load_asset("/Game/Stool/GN_Seat_Wood_002"),
        unreal.load_asset("/Game/Stool/GN_Light_Grey_Metal_002"),
    ]
    runtime.set_editor_property("MaterialOverrides", materials)
    runtime.refresh_now()
    return runtime


def spawn_camera():
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(-420.0, 520.0, 260.0),
        unreal.Rotator(-21.0, -51.0, 0.0),
    )
    camera.set_actor_label(CAMERA_LABEL)
    camera.tags = [unreal.Name("Procedural_Stool_ViewCamera")]

    camera_comp = camera.get_component_by_class(unreal.CameraComponent)
    if camera_comp:
        camera_comp.set_editor_property("field_of_view", 42.0)
    return camera


def spawn_lights():
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, 500.0), unreal.Rotator(0.0, 0.0, 0.0)
    )
    sky.set_actor_label(SKY_LABEL)
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_comp:
        sky_comp.set_editor_property("intensity", 1.35)
        sky_comp.set_editor_property("real_time_capture", True)

    key = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(-250.0, 350.0, 650.0),
        unreal.Rotator(-38.0, -32.0, 0.0),
    )
    key.set_actor_label(KEY_LABEL)
    key_comp = key.get_component_by_class(unreal.DirectionalLightComponent)
    if key_comp:
        key_comp.set_editor_property("intensity", 5.0)
        key_comp.set_editor_property("light_color", unreal.Color(255, 236, 214, 255))
        key_comp.set_editor_property("cast_shadows", True)

    fill = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(280.0, -260.0, 260.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    fill.set_actor_label(FILL_LABEL)
    fill_comp = fill.get_component_by_class(unreal.PointLightComponent)
    if fill_comp:
        fill_comp.set_editor_property("intensity", 2500.0)
        fill_comp.set_editor_property("attenuation_radius", 900.0)
        fill_comp.set_editor_property("light_color", unreal.Color(186, 215, 255, 255))


def spawn_camera_lock(camera):
    lock_class = unreal.load_class(None, "/Script/MCPGameProject.MatrixRuntimeCameraLock")
    if not lock_class:
        log("MatrixRuntimeCameraLock is unavailable; camera actor was still placed.")
        return

    lock = unreal.EditorLevelLibrary.spawn_actor_from_class(
        lock_class,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    lock.set_actor_label(CAMERA_LOCK_LABEL)
    lock.set_editor_property("CameraActor", camera)
    lock.set_editor_property("CameraTag", unreal.Name("Procedural_Stool_ViewCamera"))
    lock.set_editor_property("BlendTime", 0.0)
    lock.set_editor_property("bReapplyEveryTick", True)


def spawn_runtime_panel_host(stool):
    host_class = unreal.load_class(None, "/Script/MCPGameProject.StoolRuntimePanelHost")
    if not host_class:
        log("StoolRuntimePanelHost is unavailable; the procedural actor still works.")
        return

    host = unreal.EditorLevelLibrary.spawn_actor_from_class(
        host_class,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    host.set_actor_label(PANEL_HOST_LABEL)
    host.set_editor_property("TargetActor", stool)
    host.set_editor_property("TargetActorTag", unreal.Name(STOOL_LABEL))


def setup():
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world is open.")

    original_game_mode = world.get_world_settings().get_editor_property("default_game_mode")

    destroy_by_label({
        STOOL_LABEL,
        "Stool_DiamondMarbleActor",
        "Stool_Actor",
        CAMERA_LABEL,
        KEY_LABEL,
        FILL_LABEL,
        SKY_LABEL,
        CAMERA_LOCK_LABEL,
        PANEL_HOST_LABEL,
    })

    stool_class = unreal.load_class(None, "/Script/OpenClawBlenderGeometryNodes.BlenderGeometryNodesActor")
    if not stool_class:
        raise RuntimeError("Could not load /Script/OpenClawBlenderGeometryNodes.BlenderGeometryNodesActor")

    stool = unreal.EditorLevelLibrary.spawn_actor_from_class(
        stool_class,
        unreal.Vector(0.0, 0.0, 8.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    stool.set_actor_label(STOOL_LABEL)
    stool.tags = [unreal.Name(STOOL_LABEL)]
    configure_runtime(stool)

    spawn_lights()
    camera = spawn_camera()
    spawn_camera_lock(camera)
    spawn_runtime_panel_host(stool)

    if original_game_mode:
        world.get_world_settings().set_editor_property("default_game_mode", original_game_mode)
        log("Preserved existing GameMode override.")

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("Current level now contains the OpenClaw plugin procedural Stool.blend runtime demo.")


if __name__ == "__main__":
    setup()
