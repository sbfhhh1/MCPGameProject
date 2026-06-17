import unreal, json, os

r = {}

# 检查M_YZL_JadeDissolve的编译状态和关键连接
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    r["blend_mode"] = str(mat.get_editor_property("blend_mode"))
    
    # 获取Opacity连接的节点
    op_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["opacity_node"] = op_node.get_name() if op_node else "None"
    r["opacity_class"] = op_node.get_class().get_name() if op_node else "None"
    
    # 获取Emissive连接
    em_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["emissive_node"] = em_node.get_name() if em_node else "None"
    
    # 获取Base Color连接
    bc_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    r["base_color_node"] = bc_node.get_name() if bc_node else "None"
    
    # 获取当前材质实例的参数
    mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
    if mi:
        da = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Dissolve Amount")
        r["mi_dissolve_amount"] = da
        
        # 检查是否有任何overridden参数
        try:
            scalar_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)
            r["all_scalars"] = [{"name": str(n), "val": unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(mat, n)} for n in scalar_names]
        except: pass

with open(os.path.join(os.environ["USERPROFILE"], "debug1.json"), "w") as f:
    json.dump(r, f, indent=2)
