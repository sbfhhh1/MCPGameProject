import unreal
mel=unreal.MaterialEditingLibrary
DIR="/Game/TransformationVFX/SM2SM/jude/BurstJade"
cols={"MI_Burst_Jade_YF":unreal.LinearColor(0.14,0.34,0.15,1),"MI_Burst_Jade_TYS":unreal.LinearColor(0.20,0.32,0.12,1),"MI_Burst_Jade_YZL":unreal.LinearColor(0.12,0.30,0.12,1)}
for n,c in cols.items():
 mi=unreal.load_asset(DIR+"/"+n)
 mel.set_material_instance_vector_parameter_value(mi,"Jade Body Color",c)
 mel.set_material_instance_scalar_parameter_value(mi,"SSS Amount",0.6)
 mel.update_material_instance(mi)
 unreal.EditorAssetLibrary.save_loaded_asset(mi)
unreal.log("[Bright] jade body brightened")