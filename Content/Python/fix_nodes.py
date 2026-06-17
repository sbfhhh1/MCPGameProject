import unreal, json, os

r = {}

mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"

# 删除重建
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    unreal.EditorAssetLibrary.delete_asset(mat_path)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
source = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source)

if not mat:
    r["error"] = "dup failed"
else:
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    
    orig_e = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["orig_e"] = orig_e.get_name() if orig_e else "None"
    
    # 创建节点（不连接，不编译）
    da = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    da.set_editor_property("parameter_name", "Dissolve Amount")
    da.set_editor_property("default_value", 0.0)
    da.set_editor_property("material_expression_editor_x", -600)
    da.set_editor_property("material_expression_editor_y", -600)
    
    de = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    de.set_editor_property("parameter_name", "Dissolve Edge")
    de.set_editor_property("default_value", 0.05)
    de.set_editor_property("material_expression_editor_x", -600)
    de.set_editor_property("material_expression_editor_y", -400)
    
    dt = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    dt.set_editor_property("parameter_name", "Dissolve Tile")
    dt.set_editor_property("default_value", 0.08)
    dt.set_editor_property("material_expression_editor_x", -1200)
    dt.set_editor_property("material_expression_editor_y", -800)
    
    ec = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
    ec.set_editor_property("parameter_name", "Dissolve Edge Color")
    ec.set_editor_property("default_value", unreal.LinearColor(0.3, 0.8, 0.2, 1.0))
    ec.set_editor_property("material_expression_editor_x", -400)
    ec.set_editor_property("material_expression_editor_y", -900)
    
    gi = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    gi.set_editor_property("parameter_name", "Dissolve Glow Intensity")
    gi.set_editor_property("default_value", 2.0)
    gi.set_editor_property("material_expression_editor_x", -600)
    gi.set_editor_property("material_expression_editor_y", -1000)
    
    wp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionWorldPosition)
    wp.set_editor_property("material_expression_editor_x", -1600)
    wp.set_editor_property("material_expression_editor_y", -800)
    
    mul_tile = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_tile.set_editor_property("material_expression_editor_x", -1000)
    mul_tile.set_editor_property("material_expression_editor_y", -700)
    
    noise = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    noise.set_editor_property("material_expression_editor_x", -800)
    noise.set_editor_property("material_expression_editor_y", -700)
    
    sub = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub.set_editor_property("material_expression_editor_x", -400)
    sub.set_editor_property("material_expression_editor_y", -600)
    
    clamp_op = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionClamp)
    clamp_op.set_editor_property("clamp_mode", unreal.ClampMode.CMODE_CLAMP)
    clamp_op.set_editor_property("material_expression_editor_x", -200)
    clamp_op.set_editor_property("material_expression_editor_y", -500)
    
    sub2 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub2.set_editor_property("material_expression_editor_x", -400)
    sub2.set_editor_property("material_expression_editor_y", -800)
    
    ss_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSmoothStep)
    ss_edge.set_editor_property("material_expression_editor_x", -200)
    ss_edge.set_editor_property("material_expression_editor_y", -700)
    
    om_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionOneMinus)
    om_edge.set_editor_property("material_expression_editor_x", 0)
    om_edge.set_editor_property("material_expression_editor_y", -700)
    
    mul_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_glow.set_editor_property("material_expression_editor_x", 0)
    mul_glow.set_editor_property("material_expression_editor_y", -900)
    
    mul_final_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_final_glow.set_editor_property("material_expression_editor_x", 200)
    mul_final_glow.set_editor_property("material_expression_editor_y", -800)
    
    add_emissive = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionAdd)
    add_emissive.set_editor_property("material_expression_editor_x", 400)
    add_emissive.set_editor_property("material_expression_editor_y", -700)
    
    r["nodes_created"] = True
    
    # 连接
    unreal.MaterialEditingLibrary.connect_material_expressions(wp, "", mul_tile, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(dt, "", mul_tile, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_tile, "", noise, "World Position")
    
    unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", sub, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", sub, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", clamp_op, "None")
    unreal.MaterialEditingLibrary.connect_material_property(clamp_op, "", unreal.MaterialProperty.MP_OPACITY)
    
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", sub2, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(de, "", sub2, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(sub2, "", ss_edge, "Min")
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", ss_edge, "Max")
    unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", ss_edge, "Value")
    unreal.MaterialEditingLibrary.connect_material_expressions(ss_edge, "", om_edge, "")
    
    unreal.MaterialEditingLibrary.connect_material_expressions(ec, "", mul_glow, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(gi, "", mul_glow, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(om_edge, "", mul_final_glow, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_glow, "", mul_final_glow, "B")
    
    if orig_e:
        unreal.MaterialEditingLibrary.connect_material_expressions(orig_e, "", add_emissive, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_final_glow, "", add_emissive, "B")
    unreal.MaterialEditingLibrary.connect_material_property(add_emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    
    r["all_connected"] = True
    
    # 保存但不编译
    unreal.EditorAssetLibrary.save_asset(mat_path, only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "fix_nodes.json"), "w") as f:
    json.dump(r, f, indent=2)
