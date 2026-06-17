import unreal
LOG="[TUNE2]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
DST_PATH="/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve"
DST=unreal.EditorAssetLibrary.load_asset(DST_PATH)
MEL=unreal.MaterialEditingLibrary
def C(r,g,b): return unreal.LinearColor(r,g,b,1.0)

# 提亮的青白玉（Translucent 需要更亮）
MEL.set_material_instance_vector_parameter_value(DST,"Jade Body Color", C(0.42,0.52,0.40))
MEL.set_material_instance_vector_parameter_value(DST,"Master Tint", C(0.50,0.58,0.46))
MEL.set_material_instance_vector_parameter_value(DST,"SSS Scatter Color", C(0.62,0.70,0.55))
MEL.set_material_instance_vector_parameter_value(DST,"Pale Vein Color", C(0.70,0.78,0.62))
MEL.set_material_instance_scalar_parameter_value(DST,"SSS Amount", 0.7)
MEL.set_material_instance_scalar_parameter_value(DST,"Master Tint Amount", 0.5)
MEL.set_material_instance_scalar_parameter_value(DST,"Cloudiness", 0.35)
MEL.set_material_instance_scalar_parameter_value(DST,"Dissolve Amount", 1.0)
unreal.EditorAssetLibrary.save_asset(DST_PATH)
log("brighter celadon applied DONE")
