import unreal, json, os

r = {}

# 检查材质编译状态和shader map
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    r["name"] = mat.get_name()
    r["blend"] = str(mat.get_editor_property("blend_mode"))
    
    # 检查是否有编译错误
    try:
        exprs = mat.get_editor_property("expressions")
        r["num_expressions"] = len(exprs) if exprs else 0
    except:
        pass
    
    # 确认当前各通道连接
    for prop_name, prop_val in [
        ("Opacity", unreal.MaterialProperty.MP_OPACITY),
        ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
        ("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
    ]:
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, prop_val)
        r[f"{prop_name}_node"] = node.get_name() if node else "None"

with open(os.path.join(os.environ["USERPROFILE"], "state.json"), "w") as f:
    json.dump(r, f, indent=2)
