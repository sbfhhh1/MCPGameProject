import unreal

tools = unreal.AssetToolsHelpers.get_asset_tools()
DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
prof_path = f"{DIR}/SSP_Jade"

# 创建/加载玉石次表面 Profile
if unreal.EditorAssetLibrary.does_asset_exist(prof_path):
    prof = unreal.load_asset(prof_path)
else:
    try:
        prof = tools.create_asset("SSP_Jade", DIR, unreal.SubsurfaceProfile, unreal.SubsurfaceProfileFactory())
    except Exception as e:
        unreal.log_warning(f"[SSP] factory failed: {e}")
        prof = None

if prof:
    try:
        settings = prof.get_editor_property("settings")
        settings.set_editor_property("subsurface_color", unreal.LinearColor(0.30, 0.48, 0.20, 1.0))
        settings.set_editor_property("falloff_color", unreal.LinearColor(0.22, 0.42, 0.14, 1.0))
        settings.set_editor_property("scatter_radius", 1.2)
        prof.set_editor_property("settings", settings)
        unreal.EditorAssetLibrary.save_loaded_asset(prof)
        unreal.log("[SSP] jade subsurface profile configured")
    except Exception as e:
        unreal.log_warning(f"[SSP] settings err {e}")

# 材质改用 Subsurface Profile（基础通道正常裁剪 OpacityMask + 屏幕空间 SSS）
mat = unreal.load_asset(f"{DIR}/M_Burst_JadeDissolve")
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE_PROFILE)
if prof:
    mat.set_editor_property("subsurface_profile", prof)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[SSP] M_Burst_JadeDissolve -> Subsurface Profile + Masked")
