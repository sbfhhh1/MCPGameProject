import unreal, json, os

r = {}

mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YZL")
if mi:
    r["name"] = mi.get_name()
    r["class"] = mi.get_class().get_name()
    try:
        p = mi.get_editor_property("parent")
        r["parent"] = p.get_path_name() if p else "None"
    except Exception as e:
        r["parent_err"] = str(e)
    
    # 获取Dissolve Amount
    try:
        da = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Dissolve Amount")
        r["dissolve_amount"] = da
    except: pass
    
    # 也检查parent M_Burst_JadeDissolve
    parent = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve")
    if parent:
        r["parent_blend"] = str(parent.get_editor_property("blend_mode"))
        r["parent_shading"] = str(parent.get_editor_property("shading_model"))
        
        op = unreal.MaterialEditingLibrary.get_material_property_input_node(parent, unreal.MaterialProperty.MP_OPACITY)
        r["parent_op_node"] = op.get_name() if op else "None"
        r["parent_op_class"] = op.get_class().get_name() if op else "None"

with open(os.path.join(os.environ["USERPROFILE"], "burst_yzl.json"), "w") as f:
    json.dump(r, f, indent=2)
