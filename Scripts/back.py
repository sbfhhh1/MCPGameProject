import unreal
mel=unreal.MaterialEditingLibrary
DIR="/Game/TransformationVFX/SM2SM/jude/BurstJade"
mat=unreal.load_asset(DIR+"/M_Burst_JadeDissolve")
cols={"MI_Burst_Jade_YF":unreal.LinearColor(0.16,0.42,0.18,1),"MI_Burst_Jade_TYS":unreal.LinearColor(0.24,0.40,0.15,1),"MI_Burst_Jade_YZL":unreal.LinearColor(0.14,0.38,0.16,1)}
for n,c in cols.items():
 mi=unreal.load_asset(DIR+"/"+n)
 mel.set_material_instance_parent(mi,mat)
 mel.set_material_instance_vector_parameter_value(mi,"Jade Body Color",c)
 mel.set_material_instance_scalar_parameter_value(mi,"Dissolve Amount",1.0)
 mel.update_material_instance(mi)
 unreal.EditorAssetLibrary.save_loaded_asset(mi)
 unreal.log("[Back] "+n)