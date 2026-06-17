import unreal
LOG="[IMPMEAS]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

SSS="/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
sss_mat=unreal.EditorAssetLibrary.load_asset(SSS)
JADES={
 "jadeA": ("C:/UE_Project/MCPGameProject/Saved/_jadefbx/jadeA_ec021d65_shards.fbx", "/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65"),
 "jadeB": ("C:/UE_Project/MCPGameProject/Saved/_jadefbx/jadeB_f8ed59ab_shards.fbx", "/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab"),
 "jadeC": ("C:/UE_Project/MCPGameProject/Saved/_jadefbx/jadeC_a1276204_shards.fbx", "/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204"),
}
BASE="/Game/TransformationVFX/SM2SM/jude/Shards"
tools=unreal.AssetToolsHelpers.get_asset_tools()

for key,(fbx,origpath) in JADES.items():
    dest="{}/{}".format(BASE, key)
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
    smd=ui.static_mesh_import_data
    smd.set_editor_property("combine_meshes", False)
    smd.set_editor_property("generate_lightmap_u_vs", False)
    smd.set_editor_property("auto_generate_collision", False)
    ui.set_editor_property("static_mesh_import_data", smd)
    task.set_editor_property("options", ui)
    tools.import_asset_tasks([task])
    assets=unreal.EditorAssetLibrary.list_assets(dest, recursive=True, include_folder=False)
    n=0
    mn=[1e9]*3; mx=[-1e9]*3
    for a in assets:
        o=unreal.EditorAssetLibrary.load_asset(a)
        if isinstance(o, unreal.StaticMesh):
            o.set_material(0, sss_mat)
            unreal.EditorAssetLibrary.save_asset(a)
            b=o.get_bounding_box()
            for i,(lo,hi) in enumerate([(b.min.x,b.max.x),(b.min.y,b.max.y),(b.min.z,b.max.z)]):
                mn[i]=min(mn[i],lo); mx[i]=max(mx[i],hi)
            n+=1
    orig=unreal.EditorAssetLibrary.load_asset(origpath)
    ob=orig.get_bounding_box() if orig else None
    log("{} shards={} assembled size=({:.2f},{:.2f},{:.2f}) center=({:.2f},{:.2f},{:.2f})".format(
        key, n, mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2], (mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2))
    if ob:
        log("{} ORIG size=({:.2f},{:.2f},{:.2f}) center=({:.2f},{:.2f},{:.2f})".format(
            key, ob.max.x-ob.min.x,ob.max.y-ob.min.y,ob.max.z-ob.min.z,
            (ob.min.x+ob.max.x)/2,(ob.min.y+ob.max.y)/2,(ob.min.z+ob.max.z)/2))
log("DONE")
