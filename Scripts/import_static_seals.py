# -*- coding: utf-8 -*-
"""导入重做的 6 个印章 FBX（布尔union+重算法线），respawn actor 切到静态网格路径。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_import_static_seals.json"
ASSET_DIR = "/Game/TransformationVFX/SM2SM/ChineseSeals"
FBX_DIR = r"C:/UE_Project/MCPGameProject/SourceArt/ChineseSeals"
TOKENS = ["Shui", "Guang", "Ying", "Feng", "Yun", "Shi"]


def import_meshes():
    tasks = []
    for token in TOKENS:
        task = unreal.AssetImportTask()
        task.filename = "%s/SM_Seal_%s.fbx" % (FBX_DIR, token)
        task.destination_path = ASSET_DIR
        task.destination_name = "SM_Seal_%s" % token
        task.replace_existing = True
        task.automated = True
        task.save = True
        opts = unreal.FbxImportUI()
        opts.import_mesh = True
        opts.import_materials = False
        opts.import_textures = False
        opts.import_as_skeletal = False
        opts.static_mesh_import_data.combine_meshes = True
        opts.static_mesh_import_data.generate_lightmap_u_vs = True
        opts.static_mesh_import_data.auto_generate_collision = False
        opts.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        task.options = opts
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    loaded = []
    for token in TOKENS:
        path = "%s/SM_Seal_%s.SM_Seal_%s" % (ASSET_DIR, token, token)
        m = unreal.EditorAssetLibrary.load_asset(path)
        if m:
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            loaded.append(token)
    return loaded


def respawn_static():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old = None
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() == "ChineseSealPoolAnimator":
            old = a
            break
    if not old:
        raise RuntimeError("actor not found")

    loc = old.get_actor_location()
    rot = old.get_actor_rotation()
    tags = list(old.tags)
    # 复制布局/动画参数
    props = ["Rows", "Columns", "RowSpacing", "ColumnSpacing", "SealScale",
             "SealHeightToSectionRatio", "HeightAboveWater", "bEnableAnimation",
             "bAnimateInEditor", "AnimationAmplitude", "AnimationSpeed",
             "AnimationFrequency", "Irregularity", "NoiseScale", "RandomSeed"]
    saved = {}
    for p in props:
        try:
            saved[p] = old.get_editor_property(p)
        except Exception:
            pass

    cls = old.get_class()
    sub.destroy_actor(old)
    new = sub.spawn_actor_from_class(cls, loc, rot)
    new.set_actor_label("Chinese_Seal_Pool_Animator")
    if tags:
        new.tags = tags
    # 不设 SealMeshes：构造函数 LoadDefaultMeshesIfNeeded 已自动加载静态网格
    for p, v in saved.items():
        try:
            new.set_editor_property(p, v)
        except Exception:
            pass

    sm = new.get_components_by_class(unreal.StaticMeshComponent)
    pm = new.get_components_by_class(unreal.ProceduralMeshComponent)
    seal_meshes = new.get_editor_property("SealMeshes")
    return {
        "static_components": len(sm),
        "procedural_components": len(pm),
        "seal_meshes_count": len(seal_meshes) if seal_meshes else 0,
    }


def main():
    loaded = import_meshes()
    info = respawn_static()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    try:
        unreal.EditorLevelLibrary.save_current_level()
    except Exception:
        pass
    result = {"imported": loaded, **info}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    unreal.log("[import_static_seals] " + json.dumps(result, default=str))


if __name__ == "__main__":
    main()
