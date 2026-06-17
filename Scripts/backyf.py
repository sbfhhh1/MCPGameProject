import unreal
mel=unreal.MaterialEditingLibrary
DIR="/Game/TransformationVFX/SM2SM/jude/BurstJade"
mat=unreal.load_asset(DIR+"/M_Burst_JadeDissolve")
mi=unreal.load_asset(DIR+"/MI_Burst_Jade_YF")
mel.set_material_instance_parent(mi,mat)
mel.set_material_instance_vector_parameter_value(mi,"Jade Body Color",unreal.LinearColor(0.16,0.42,0.18,1))
mel.set_material_instance_scalar_parameter_value(mi,"Dissolve Amount",1.0)
mel.update_material_instance(mi)
unreal.EditorAssetLibrary.save_loaded_asset(mi)
unreal.log("[BackYF] ok")