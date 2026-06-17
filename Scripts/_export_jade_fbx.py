import unreal, os
LOG="[EXPFBX]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
OUT_DIR="C:/UE_Project/MCPGameProject/Saved/_jadefbx"
os.makedirs(OUT_DIR, exist_ok=True)
MESHES={
 "jadeA_ec021d65":"/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65",
 "jadeB_f8ed59ab":"/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab",
 "jadeC_a1276204":"/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204",
}
for name,path in MESHES.items():
    mesh=unreal.EditorAssetLibrary.load_asset(path)
    if not mesh:
        log("MISSING {}".format(path)); continue
    out=os.path.join(OUT_DIR, name+".fbx")
    task=unreal.AssetExportTask()
    task.set_editor_property("object", mesh)
    task.set_editor_property("filename", out)
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("replace_identical", True)
    opt=unreal.FbxExportOption()
    opt.set_editor_property("collision", False)
    opt.set_editor_property("level_of_detail", False)
    task.set_editor_property("options", opt)
    task.set_editor_property("exporter", unreal.StaticMeshExporterFBX())
    ok=unreal.Exporter.run_asset_export_task(task)
    log("export {} -> {} ok={}".format(name, out, ok))
log("DONE")
