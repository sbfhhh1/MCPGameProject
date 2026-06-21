# -*- coding: utf-8 -*-
import json
import os
import unreal

ASSET_DIR = "/Game/TransformationVFX/SM2SM/ChineseSeals"
FBX_DIR = r"C:/UE_Project/MCPGameProject/SourceArt/ChineseSeals"
OUT = r"C:/UE_Project/MCPGameProject/Scripts/_chinese_seal_pool_setup.json"

LABEL = "Chinese_Seal_Pool_Animator"
WATER_LOCATION = unreal.Vector(350.0, 0.0, 60.0)

SEAL_TOKENS = ["Shui", "Guang", "Ying", "Feng", "Yun", "Shi"]


def log(msg):
    unreal.log("[ChineseSealPool] " + msg)


def ensure_dir():
    if not unreal.EditorAssetLibrary.does_directory_exist(ASSET_DIR):
        unreal.EditorAssetLibrary.make_directory(ASSET_DIR)


def import_meshes():
    ensure_dir()
    tasks = []
    for token in SEAL_TOKENS:
        fbx_path = os.path.join(FBX_DIR, "SM_Seal_{}.fbx".format(token)).replace("\\", "/")
        task = unreal.AssetImportTask()
        task.filename = fbx_path
        task.destination_path = ASSET_DIR
        task.destination_name = "SM_Seal_{}".format(token)
        task.replace_existing = True
        task.automated = True
        task.save = True

        opts = unreal.FbxImportUI()
        opts.import_mesh = True
        opts.import_materials = True
        opts.import_textures = False
        opts.import_as_skeletal = False
        opts.static_mesh_import_data.combine_meshes = True
        opts.static_mesh_import_data.generate_lightmap_u_vs = True
        opts.static_mesh_import_data.auto_generate_collision = False
        task.options = opts
        tasks.append(task)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    meshes = []
    for token in SEAL_TOKENS:
        path = "{}/SM_Seal_{}.SM_Seal_{}".format(ASSET_DIR, token, token)
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if mesh:
            try:
                mesh.set_editor_property("nanite_settings", mesh.get_editor_property("nanite_settings"))
            except Exception:
                pass
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            meshes.append(mesh)
        else:
            unreal.log_warning("[ChineseSealPool] Missing imported mesh: " + path)
    return meshes


def destroy_existing():
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() == LABEL:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass


def setup():
    meshes = import_meshes()
    if not meshes:
        raise RuntimeError("No Chinese seal meshes were imported.")

    actor_class = unreal.load_class(None, "/Script/MCPGameProject.ChineseSealPoolAnimator")
    if not actor_class:
        raise RuntimeError("AChineseSealPoolAnimator class is not loaded. Recompile the project/editor module.")

    destroy_existing()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        WATER_LOCATION,
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(LABEL)
    actor.tags = [unreal.Name("WaterPool"), unreal.Name("ChineseSealPool")]

    actor.set_editor_property("SealMeshes", meshes)
    actor.set_editor_property("Rows", 4)
    actor.set_editor_property("Columns", 4)
    actor.set_editor_property("RowSpacing", 70.0)
    actor.set_editor_property("ColumnSpacing", 70.0)
    actor.set_editor_property("SealScale", 0.75)
    actor.set_editor_property("HeightAboveWater", 3.0)
    actor.set_editor_property("AnimationAmplitude", 4.5)
    actor.set_editor_property("AnimationSpeed", 0.32)
    actor.set_editor_property("AnimationFrequency", 1.0)
    actor.set_editor_property("Irregularity", 0.68)
    actor.set_editor_property("NoiseScale", 0.55)
    actor.set_editor_property("RandomSeed", 1937)
    actor.set_editor_property("bEnableAnimation", True)
    actor.set_editor_property("bAnimateInEditor", True)
    actor.rerun_construction_scripts()

    unreal.EditorAssetLibrary.save_directory(ASSET_DIR, only_if_is_dirty=False, recursive=True)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    try:
        unreal.EditorLevelLibrary.save_current_level()
    except Exception as exc:
        unreal.log_warning("[ChineseSealPool] save_current_level failed: " + str(exc))

    result = {
        "actor_label": actor.get_actor_label(),
        "actor_name": actor.get_name(),
        "class": actor.get_class().get_name(),
        "location": [WATER_LOCATION.x, WATER_LOCATION.y, WATER_LOCATION.z],
        "rows": 4,
        "columns": 4,
        "mesh_count": len(meshes),
        "asset_dir": ASSET_DIR,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    log("setup complete: " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        setup()
    except Exception as exc:
        import traceback

        tb = traceback.format_exc()
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"error": str(exc), "traceback": tb}, fh, ensure_ascii=False, indent=2)
        unreal.log_error("[ChineseSealPool] " + tb)
        raise
