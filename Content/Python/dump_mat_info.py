import unreal
import json
import os

# 获取M_YZL_ProceduralJade_SSS的材质信息
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
mat = unreal.load_asset(mat_path)
result = {"path": mat_path, "name": mat.get_name() if mat else "NOT_FOUND"}

if mat:
    result["class"] = mat.get_class().get_name()
    # 尝试获取材质属性
    try:
        result["blend_mode"] = str(mat.get_editor_property("blend_mode"))
    except: pass
    try:
        result["shading_model"] = str(mat.get_editor_property("shading_model"))
    except: pass
    try:
        result["two_sided"] = str(mat.get_editor_property("two_sided"))
    except: pass
    # 获取材质表达式
    try:
        expressions = mat.get_editor_property("expression_collection")
        if expressions:
            result["num_expressions"] = len(expressions.expressions) if hasattr(expressions, 'expressions') else "unknown"
    except Exception as e:
        result["expression_error"] = str(e)

# 获取M_Burst_JadeDissolve的材质信息
dissolve_path = "/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve"
dissolve_mat = unreal.load_asset(dissolve_path)
result["dissolve_mat"] = {"path": dissolve_path, "name": dissolve_mat.get_name() if dissolve_mat else "NOT_FOUND"}
if dissolve_mat:
    result["dissolve_mat"]["class"] = dissolve_mat.get_class().get_name()
    try:
        result["dissolve_mat"]["blend_mode"] = str(dissolve_mat.get_editor_property("blend_mode"))
    except: pass
    try:
        result["dissolve_mat"]["shading_model"] = str(dissolve_mat.get_editor_property("shading_model"))
    except: pass

# 获取MI_Burst_Jade_YZL材质实例信息
mi_path = "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YZL"
mi = unreal.load_asset(mi_path)
result["mi_burst_yzl"] = {"path": mi_path, "name": mi.get_name() if mi else "NOT_FOUND"}
if mi:
    result["mi_burst_yzl"]["class"] = mi.get_class().get_name()
    try:
        parent = mi.get_editor_property("parent")
        if parent:
            result["mi_burst_yzl"]["parent"] = parent.get_path_name()
    except: pass

# 获取MI_YZL_AncientJade信息
mi_yzl_path = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"
mi_yzl = unreal.load_asset(mi_yzl_path)
result["mi_yzl_ancient"] = {"path": mi_yzl_path, "name": mi_yzl.get_name() if mi_yzl else "NOT_FOUND"}
if mi_yzl:
    result["mi_yzl_ancient"]["class"] = mi_yzl.get_class().get_name()
    try:
        parent = mi_yzl.get_editor_property("parent")
        if parent:
            result["mi_yzl_ancient"]["parent"] = parent.get_path_name()
    except: pass

# 也查看M_Burst_JadeFinal
final_path = "/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeFinal"
final_mat = unreal.load_asset(final_path)
result["final_mat"] = {"path": final_path, "name": final_mat.get_name() if final_mat else "NOT_FOUND"}
if final_mat:
    result["final_mat"]["class"] = final_mat.get_class().get_name()
    try:
        result["final_mat"]["blend_mode"] = str(final_mat.get_editor_property("blend_mode"))
    except: pass
    try:
        result["final_mat"]["shading_model"] = str(final_mat.get_editor_property("shading_model"))
    except: pass

out_path = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\lafa"), "ue5_mat_info.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
