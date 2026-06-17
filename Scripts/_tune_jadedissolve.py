import unreal
LOG="[TUNE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

SRC = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
DST_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve"
DST = unreal.EditorAssetLibrary.load_asset(DST_PATH)
MEL = unreal.MaterialEditingLibrary

# 拷贝标量
for s in SRC.get_editor_property("scalar_parameter_values"):
    nm = s.get_editor_property("parameter_info").get_editor_property("name")
    v = s.get_editor_property("parameter_value")
    try:
        MEL.set_material_instance_scalar_parameter_value(DST, nm, v)
        log("scalar {} = {}".format(nm, v))
    except Exception as e:
        log("scalar {} ERR {}".format(nm, e))
# 拷贝向量
for s in SRC.get_editor_property("vector_parameter_values"):
    nm = s.get_editor_property("parameter_info").get_editor_property("name")
    v = s.get_editor_property("parameter_value")
    try:
        MEL.set_material_instance_vector_parameter_value(DST, nm, v)
        log("vector {} = ({:.3f},{:.3f},{:.3f})".format(nm, v.r,v.g,v.b))
    except Exception as e:
        log("vector {} ERR {}".format(nm, e))

# Dissolve 默认显示
MEL.set_material_instance_scalar_parameter_value(DST, "Dissolve Amount", 1.0)
log("set Dissolve Amount = 1.0")

unreal.EditorAssetLibrary.save_asset(DST_PATH)
log("saved DONE")
