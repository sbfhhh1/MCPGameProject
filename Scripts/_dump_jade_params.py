import unreal
LOG="[JPARAM]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

def dump_instance(path):
    mi = unreal.EditorAssetLibrary.load_asset(path)
    log("=== {} ===".format(path.split('/')[-1]))
    try:
        svals = mi.get_editor_property("scalar_parameter_values")
        for s in svals:
            info = s.get_editor_property("parameter_info")
            nm = info.get_editor_property("name")
            v = s.get_editor_property("parameter_value")
            log("  SCALAR {} = {}".format(nm, v))
    except Exception as e:
        log("  scalar err {}".format(e))
    try:
        vvals = mi.get_editor_property("vector_parameter_values")
        for s in vvals:
            info = s.get_editor_property("parameter_info")
            nm = info.get_editor_property("name")
            v = s.get_editor_property("parameter_value")
            log("  VECTOR {} = ({:.3f},{:.3f},{:.3f},{:.3f})".format(nm, v.r,v.g,v.b,v.a))
    except Exception as e:
        log("  vector err {}".format(e))

def dump_mat_param_names(path):
    m = unreal.EditorAssetLibrary.load_asset(path)
    log("=== PARAM NAMES of {} ===".format(path.split('/')[-1]))
    try:
        sn = unreal.MaterialEditingLibrary.get_scalar_parameter_names(m)
        log("  SCALARS: {}".format([str(x) for x in sn]))
    except Exception as e:
        log("  scalar names err {}".format(e))
    try:
        vn = unreal.MaterialEditingLibrary.get_vector_parameter_names(m)
        log("  VECTORS: {}".format([str(x) for x in vn]))
    except Exception as e:
        log("  vector names err {}".format(e))

dump_instance("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
dump_instance("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
dump_mat_param_names("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
log("DONE")
