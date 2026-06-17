import unreal
m=unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve")
unreal.log("[Chk] shading="+str(m.get_editor_property("shading_model"))+" blend="+str(m.get_editor_property("blend_mode")))
p=m.get_editor_property("subsurface_profile")
unreal.log("[Chk] profile="+(p.get_name() if p else "None"))
unreal.log("[Chk] sspexists="+str(unreal.EditorAssetLibrary.does_asset_exist("/Game/TransformationVFX/SM2SM/jude/BurstJade/SSP_Jade")))