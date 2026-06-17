import unreal
LOG="[TUNE3]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
DST_PATH="/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve"
DST=unreal.EditorAssetLibrary.load_asset(DST_PATH)
MEL=unreal.MaterialEditingLibrary
def C(r,g,b): return unreal.LinearColor(r,g,b,1.0)

# 恢复 SSS 层次：体色中等青、散射色明显更亮拉开对比、SSS拉满、不要统一tint糊平
MEL.set_material_instance_scalar_parameter_value(DST,"Master Tint Amount", 0.0)
MEL.set_material_instance_vector_parameter_value(DST,"Jade Body Color", C(0.16,0.30,0.20))
MEL.set_material_instance_vector_parameter_value(DST,"Master Tint", C(0.20,0.34,0.22))
MEL.set_material_instance_vector_parameter_value(DST,"SSS Scatter Color", C(0.62,0.74,0.50))
MEL.set_material_instance_vector_parameter_value(DST,"Pale Vein Color", C(0.55,0.62,0.42))
MEL.set_material_instance_scalar_parameter_value(DST,"SSS Amount", 1.0)
MEL.set_material_instance_scalar_parameter_value(DST,"Cloudiness", 0.45)
MEL.set_material_instance_scalar_parameter_value(DST,"Ochre Stain Amount", 0.30)
MEL.set_material_instance_scalar_parameter_value(DST,"Polished Roughness", 0.06)
MEL.set_material_instance_scalar_parameter_value(DST,"Dissolve Amount", 1.0)
unreal.EditorAssetLibrary.save_asset(DST_PATH)
log("SSS-depth retune applied DONE")
