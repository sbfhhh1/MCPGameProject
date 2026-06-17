import unreal
mel=unreal.MaterialEditingLibrary
DIR="/Game/TransformationVFX/SM2SM/jude/BurstJade"
for nm in ["M_Burst_JadeFinal","M_Burst_JadeDissolve"]:
 ex=unreal.EditorAssetLibrary.does_asset_exist(DIR+"/"+nm)
 if ex:
  m=unreal.load_asset(DIR+'/'+nm)
  unreal.log("[St] "+nm+" blend="+str(m.get_editor_property("blend_mode"))+" shading="+str(m.get_editor_property("shading_model"))+" params="+str(len(mel.get_scalar_parameter_names(m))+len(mel.get_vector_parameter_names(m))))
 else:
  unreal.log("[St] "+nm+" MISSING")
for n in ["MI_Burst_Jade_YF","MI_Burst_Jade_TYS","MI_Burst_Jade_YZL"]:
 mi=unreal.load_asset(DIR+"/"+n)
 p=mi.get_editor_property("parent")
 unreal.log("[St] "+n+" parent="+(p.get_name() if p else "None"))