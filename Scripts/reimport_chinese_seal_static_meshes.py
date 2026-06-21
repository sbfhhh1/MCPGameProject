# -*- coding: utf-8 -*-
import json
import os
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_reimport_chinese_seal_static_meshes.json"
SRC_DIR = r"C:/UE_Project/MCPGameProject/SourceArt/ChineseSeals"
DEST_DIR = "/Game/TransformationVFX/SM2SM/ChineseSeals"

TOKENS = [
    "Chuan",
    "Di",
    "Dian",
    "Feng",
    "Guang",
    "Hai",
    "Huo",
    "Lei",
    "Lin",
    "Ri",
    "Shan",
    "Shi",
    "Shui",
    "Tian",
    "Xing",
    "Xue",
    "Ying",
    "Yu",
    "Yue",
    "Yun",
]


def make_options():
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("automated_import_should_detect_type", False)
    if hasattr(unreal, "FBXImportType"):
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)

    static_data = options.get_editor_property("static_mesh_import_data")
    if static_data:
        for prop, value in (
            ("combine_meshes", True),
            ("generate_lightmap_u_vs", True),
            ("auto_generate_collision", False),
        ):
            try:
                static_data.set_editor_property(prop, value)
            except Exception:
                pass
        if hasattr(unreal, "FBXNormalImportMethod"):
            try:
                static_data.set_editor_property(
                    "normal_import_method",
                    unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
                )
            except Exception:
                pass
    return options


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(DEST_DIR):
        unreal.EditorAssetLibrary.make_directory(DEST_DIR)

    tasks = []
    for token in TOKENS:
        name = "SM_Seal_" + token
        filename = os.path.join(SRC_DIR, name + ".fbx")
        if not os.path.exists(filename):
            raise RuntimeError("Missing FBX: " + filename)

        task = unreal.AssetImportTask()
        task.set_editor_property("filename", filename)
        task.set_editor_property("destination_path", DEST_DIR)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("replace_existing_settings", False)
        task.set_editor_property("save", True)
        task.set_editor_property("options", make_options())
        tasks.append(task)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    imported = []
    for token in TOKENS:
        path = DEST_DIR + "/SM_Seal_" + token
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if asset:
            unreal.EditorAssetLibrary.save_loaded_asset(asset)
            imported.append(path)

    result = {"requested": len(TOKENS), "imported": imported}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[ReimportChineseSealStaticMeshes] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
