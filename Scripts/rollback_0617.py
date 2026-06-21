# -*- coding: utf-8 -*-
"""回到纯06-17：玉石Dissolve回0.0 + BP_Burst_SM移除FistDisplayToggle组件。结果写UE日志。"""
import unreal, json

JADE = [
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YF_Jade_TYS_SSS",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_TYS_SSS",
]
BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"

result = {"jade": [], "bp_component_removed": False}

# 1. 玉石 Dissolve 回 0.0（撤销我改的1.0）
for p in JADE:
    m = unreal.EditorAssetLibrary.load_asset(p)
    if m:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m, "Dissolve Amount", 0.0)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        result["jade"].append({p.split("/")[-1]: m.get_scalar_parameter_value("Dissolve Amount")})

# 2. BP 移除 FistDisplayToggle 组件
bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
if bp:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    target = None
    for h in handles:
        data = sub.k2_find_subobject_data_from_handle(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if obj and obj.get_class().get_name() == "FistDisplayToggleComponent":
            target = h
            break
    if target:
        sub.delete_subobject(handles[0], target, bp)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        result["bp_component_removed"] = True

unreal.log("[rollback_0617] " + json.dumps(result, default=str))
