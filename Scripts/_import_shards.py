import unreal
LOG="[IMPSHARD]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

SSS="/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
sss_mat=unreal.EditorAssetLibrary.load_asset(SSS)
JADES={
 "jadeA": "C:/UE_Project/MCPGameProject/Saved/_jadefbx/jadeA_ec021d65_shards.fbx",
 "jadeB": "C:/UE_Project/MCPGameProject/Saved/_jadefbx/jadeB_f8ed59ab_shards.fbx",
 "jadeC": "C:/UE_Project/MCPGameProject/Saved/_jadefbx/jadeC_a1276204_shards.fbx",
}
BASE="/Game/TransformationVFX/SM2SM/jude/Shards"
tools=unreal.AssetToolsHelpers.get_asset_tools()

for key,fbx in JADES.items():
    dest="{}/{}".format(BASE, key)
    # 清旧
    if unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.EditorAssetLibrary.delete_directory(dest)
    task=unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    ui=unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    sm_data=ui.static_mesh_import_data
    sm_data.set_editor_property("combine_meshes", False)
    sm_data.set_editor_property("generate_lightmap_u_vs", False)
    sm_data.set_editor_property("auto_generate_collision", False)
    ui.set_editor_property("static_mesh_import_data", sm_data)
    task.set_editor_property("options", ui)
    tools.import_asset_tasks([task])
    imported=task.get_editor_property("imported_object_paths")
    log("{} imported {} assets to {}".format(key, len(imported) if imported else 0, dest))
    # 给每个网格设 SSS 材质
    assets=unreal.EditorAssetLibrary.list_assets(dest, recursive=True, include_folder=False)
    n=0
    for a in assets:
        obj=unreal.EditorAssetLibrary.load_asset(a)
        if isinstance(obj, unreal.StaticMesh):
            obj.set_material(0, sss_mat)
            unreal.EditorAssetLibrary.save_asset(a)
            n+=1
    log("{} set SSS on {} static meshes".format(key, n))

log("DONE")
