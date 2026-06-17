import unreal, json, os

r = {}

# 分析M_Burst_JadeDissolve的溶解实现
ref = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_Burst_JadeDissolve")
if ref:
    r["name"] = ref.get_name()
    r["blend"] = str(ref.get_editor_property("blend_mode"))
    r["shading_model"] = str(ref.get_editor_property("shading_model"))
    
    # 检查关键连接
    op_node = unreal.MaterialEditingLibrary.get_material_property_input_node(ref, unreal.MaterialProperty.MP_OPACITY)
    r["opacity_node"] = op_node.get_name() if op_node else "None"
    r["opacity_class"] = op_node.get_class().get_name() if op_node else "None"
    
    em_node = unreal.MaterialEditingLibrary.get_material_property_input_node(ref, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["emissive_node"] = em_node.get_name() if em_node else "None"
    
    # 获取参数列表
    try:
        sn = unreal.MaterialEditingLibrary.get_scalar_parameter_names(ref)
        r["scalar_params"] = [{"name": str(n), "val": unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(ref, n)} for n in sn]
    except Exception as e:
        r["scalar_err"] = str(e)
    
    try:
        vn = unreal.MaterialEditingLibrary.get_vector_parameter_names(ref)
        r["vector_params"] = [{"name": str(n), "val": str(unreal.MaterialEditingLibrary.get_material_default_vector_parameter_value(ref, n))} for n in vn]
    except Exception as e:
        r["vector_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ref_dissolve.json"), "w") as f:
    json.dump(r, f, indent=2)
