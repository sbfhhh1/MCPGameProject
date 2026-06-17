import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
if mat:
    r["blend"] = str(mat.get_editor_property("blend_mode"))
    r["shading"] = str(mat.get_editor_property("shading_model"))
    r["num_expr"] = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    
    # 检查关键属性连接
    bc = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    r["base_color"] = bc.get_name() if bc else "None"
    
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["opacity"] = op.get_name() if op else "None"

with open(os.path.join(os.environ["USERPROFILE"], "orig_mat_check.json"), "w") as f:
    json.dump(r, f, indent=2)
