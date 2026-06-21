"""在当前 SM2SM 关卡里放置梯田等高线地形（Blender GN 程序化网格 + 引擎侧 WallNoise 缓慢起伏）。
放置在 frame 画框开口中心，正面朝 -X（正对玩家相机）。
参考案例：setup_procedural_stool_runtime_scene.py。
"""
import json
import unreal

LABEL = "Terrace_Terrain"
ASSET_DIR = "/Game/TerraceTerrain"
MAT_NAME = "M_TerraceTerrain"
OUT = r"C:/UE_Project/MCPGameProject/Scripts/_terrace_setup_out.json"

BLEND_FILE = r"C:/UE_Project/MCPGameProject/Content/BlenderFile/terrace_terrain_gn.blend"
SIDECAR = r"C:/UE_Project/MCPGameProject/Plugins/OpenClawBlenderGeometryNodes/Content/Python/unreal_gn_eval.py"
BLENDER_EXE = r"C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"

# frame 画框开口中心 [127,0,160]；放到画框深度后部 X=150，浮雕向 -X 凸出朝玩家
LOCATION = unreal.Vector(150.0, 0.0, 160.0)
SCALE = unreal.Vector(1.5, 1.5, 1.5)


def log(msg):
    unreal.log("[TerraceTerrain] " + msg)


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def make_material():
    path = f"{ASSET_DIR}/{MAT_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(MAT_NAME, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant4Vector)
    base.set_editor_property("constant", unreal.LinearColor(0.72, 0.60, 0.42, 1.0))  # 暖砂色
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.set_editor_property("r", 0.85)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def destroy_existing():
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() == LABEL:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass


def setup():
    ensure_dir(ASSET_DIR)
    mat = make_material()
    destroy_existing()

    actor_class = unreal.load_class(None, "/Script/OpenClawBlenderGeometryNodes.BlenderGeometryNodesActor")
    if not actor_class:
        raise RuntimeError("Could not load BlenderGeometryNodesActor class")

    rot = unreal.Rotator()
    rot.pitch = -90.0
    rot.yaw = 0.0
    rot.roll = 0.0

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, LOCATION, rot)
    actor.set_actor_label(LABEL)
    actor.tags = [unreal.Name(LABEL)]
    actor.set_actor_scale3d(SCALE)

    runtime = actor.get_component_by_class(unreal.BlenderGeometryNodesComponent)
    if not runtime:
        raise RuntimeError("Actor has no BlenderGeometryNodesComponent")
    runtime.set_editor_property("BlenderExecutable", BLENDER_EXE)
    runtime.set_editor_property("BlendFile", unreal.FilePath(BLEND_FILE))
    runtime.set_editor_property("ObjectName", "TerraceTerrain")
    runtime.set_editor_property("ModifierName", "GN_Terrace")
    runtime.set_editor_property("SidecarScriptPath", SIDECAR)
    runtime.set_editor_property("RefreshMode", unreal.BlenderGNRefreshMode.MANUAL)
    runtime.set_editor_property("BlenderTimeoutSeconds", 60)
    runtime.set_editor_property("bUseBinaryMeshCache", True)
    runtime.set_editor_property("bApplyImportedNormals", True)
    runtime.set_editor_property("bSmoothNormalsByPosition", False)
    runtime.set_editor_property("bEnablePreviewAnimation", False)
    runtime.set_editor_property("bRefreshOnBeginPlay", True)
    runtime.set_editor_property("bCastShadows", True)
    runtime.set_editor_property("BlenderToUnrealScale", 100.0)
    runtime.set_editor_property("MaterialOverrides", [mat])

    runtime.refresh_now()

    # 引擎侧 WallNoise 缓慢起伏（沿局部 Z = 浮雕轴），PIE 时播放。
    # UE5.1 用 SubobjectDataSubsystem 添加持久组件。
    wall_added = False
    try:
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = sds.k2_gather_subobject_data_for_instance(actor)
        root_handle = handles[0]
        params = unreal.AddNewSubobjectParams(
            parent_handle=root_handle,
            new_class=unreal.BlenderGNWallNoiseMotionComponent,
        )
        sds.add_new_subobject(params)
        wall = actor.get_component_by_class(unreal.BlenderGNWallNoiseMotionComponent)
        if wall:
            wall.set_editor_property("Runtime", runtime)
            wall.set_editor_property("bLiveMotion", True)
            wall.set_editor_property("DisplacementAxis", unreal.BlenderGNDisplacementAxis.Z)
            wall.set_editor_property("Strength", 10.0)
            wall.set_editor_property("Speed", 0.22)
            wall.set_editor_property("Scale", 1.6)
            wall.set_editor_property("Smoothness", 0.6)
            wall.set_editor_property("MaxAnimationFrameRate", 30.0)
            wall_added = True
    except Exception as exc:
        unreal.log_warning("[TerraceTerrain] WallNoise add failed: " + str(exc))

    out = {
        "spawned": actor.get_name(),
        "label": actor.get_actor_label(),
        "location": [LOCATION.x, LOCATION.y, LOCATION.z],
        "rotation": [rot.pitch, rot.yaw, rot.roll],
        "scale": [SCALE.x, SCALE.y, SCALE.z],
        "blend": BLEND_FILE,
        "wall_added": wall_added,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    log("placed Terrace_Terrain and triggered refresh_now")


if __name__ == "__main__":
    import traceback
    try:
        setup()
    except Exception as exc:
        tb = traceback.format_exc()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"error": str(exc), "traceback": tb}, f, indent=2)
        unreal.log_error("[TerraceTerrain] " + tb)
        raise
