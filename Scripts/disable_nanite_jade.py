import unreal

paths = [
    "/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65",
    "/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab",
    "/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204",
]
for p in paths:
    sm = unreal.load_asset(p)
    if not sm:
        unreal.log_warning(f"[NoNanite] missing {p}")
        continue
    ns = sm.get_editor_property("nanite_settings")
    ns.set_editor_property("enabled", False)
    sm.set_editor_property("nanite_settings", ns)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    unreal.log(f"[NoNanite] {sm.get_name()} Nanite disabled")

unreal.log("[NoNanite] DONE")
