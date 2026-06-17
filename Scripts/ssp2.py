import unreal
m=unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve")
m.set_editor_property("shading_model",unreal.MaterialShadingModel.MSM_SUBSURFACE_PROFILE)
unreal.MaterialEditingLibrary.recompile_material(m)
unreal.EditorAssetLibrary.save_loaded_asset(m)
unreal.log("[SSP2] shading=SubsurfaceProfile set")