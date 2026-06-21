# -*- coding: utf-8 -*-
"""导入20个印章FBX，让pool显示20种字：set SealMeshes(持久) + 手动改组件网格(立即可见)。不碰C++。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_setup_20_seals.json"
ASSET_DIR = "/Game/TransformationVFX/SM2SM/ChineseSeals"
FBX_DIR = r"C:/UE_Project/MCPGameProject/SourceArt/ChineseSeals"
TOKENS = ["Shui", "Guang", "Ying", "Feng", "Yun", "Shi", "Huo", "Shan", "Hai", "Lin",
          "Lei", "Dian", "Yu", "Xue", "Yue", "Ri", "Xing", "Tian", "Di", "Chuan"]


def main():
    world = unreal.EditorLevelLibrary.get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "Interchange.FeatureFlags.Import.FBX 0")

    # 1. 导入20个FBX
    tasks = []
    for token in TOKENS:
        t = unreal.AssetImportTask()
        t.filename = "%s/SM_Seal_%s.fbx" % (FBX_DIR, token)
        t.destination_path = ASSET_DIR
        t.destination_name = "SM_Seal_%s" % token
        t.replace_existing = True
        t.automated = True
        t.save = True
        o = unreal.FbxImportUI()
        o.import_mesh = True
        o.import_materials = False
        o.import_textures = False
        o.import_as_skeletal = False
        o.static_mesh_import_data.combine_meshes = True
        o.static_mesh_import_data.generate_lightmap_u_vs = True
        o.static_mesh_import_data.auto_generate_collision = False
        o.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        t.options = o
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    meshes = []
    for token in TOKENS:
        m = unreal.EditorAssetLibrary.load_asset("%s/SM_Seal_%s.SM_Seal_%s" % (ASSET_DIR, token, token))
        if m:
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            meshes.append(m)
    if len(meshes) != 20:
        result = {"error": "only loaded %d meshes" % len(meshes)}
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        return

    # 2. 找pool
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pool = None
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() == "ChineseSealPoolAnimator":
            pool = a
            break
    if not pool:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"error": "pool not found"}, fh)
        return

    # 3. set SealMeshes=20（持久化：重载后 RebuildSeals 用这20个）
    pool.set_editor_property("SealMeshes", meshes)
    pool.set_editor_property("bEnableAnimation", True)
    pool.set_editor_property("bAnimateInEditor", True)

    # 4. 手动改现有组件网格循环20种（立即可见，组件是Transient不影响持久）
    comps = pool.get_components_by_class(unreal.StaticMeshComponent)
    changed = 0
    for i, c in enumerate(comps):
        c.set_static_mesh(meshes[i % 20])
        changed += 1

    # 5. 保存关卡
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    saved = False
    try:
        saved = bool(unreal.EditorLevelLibrary.save_current_level())
    except Exception as e:
        saved = "ERR:" + str(e)

    # 统计当前组件用的网格种类
    kinds = set()
    for c in comps:
        m = c.get_editor_property("static_mesh")
        if m:
            kinds.add(m.get_name())

    result = {
        "meshes_loaded": len(meshes),
        "static_components": len(comps),
        "components_changed": changed,
        "distinct_meshes_now": len(kinds),
        "seal_meshes_set": len(pool.get_editor_property("SealMeshes")),
        "level_saved": saved,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    unreal.log("[setup_20_seals] " + json.dumps(result, default=str))


if __name__ == "__main__":
    main()
