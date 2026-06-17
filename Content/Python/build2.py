import unreal, json, os

# 先删除重建
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    unreal.EditorAssetLibrary.delete_asset(mat_path)

# 重新复制
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
source = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source)

r = {"step": "init"}

if not mat:
    r["error"] = "duplicate failed"
else:
    # 修改Blend Mode
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    
    # 获取原有的Emissive Color连接
    orig_emissive_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, "emissive_color")
    r["orig_emissive"] = orig_emissive_node.get_name() if orig_emissive_node else "None"
    
    # 获取opacity当前连接
    orig_opacity_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, "opacity")
    r["orig_opacity"] = orig_opacity_node.get_name() if orig_opacity_node else "None"
    
    # ========= 创建溶解节点 =========
    
    # Dissolve Amount
    da = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    da.set_editor_property("parameter_name", "Dissolve Amount")
    da.set_editor_property("default_value", 0.0)
    da.set_editor_property("material_expression_editor_x", -800)
    da.set_editor_property("material_expression_editor_y", -600)
    
    # Dissolve Edge
    de = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    de.set_editor_property("parameter_name", "Dissolve Edge")
    de.set_editor_property("default_value", 0.05)
    de.set_editor_property("material_expression_editor_x", -800)
    de.set_editor_property("material_expression_editor_y", -400)
    
    # Dissolve Edge Color
    ec = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
    ec.set_editor_property("parameter_name", "Dissolve Edge Color")
    ec.set_editor_property("default_value", unreal.LinearColor(0.3, 0.8, 0.2, 1.0))
    ec.set_editor_property("material_expression_editor_x", -400)
    ec.set_editor_property("material_expression_editor_y", -900)
    
    # Dissolve Glow Intensity
    gi = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    gi.set_editor_property("parameter_name", "Dissolve Glow Intensity")
    gi.set_editor_property("default_value", 2.0)
    gi.set_editor_property("material_expression_editor_x", -600)
    gi.set_editor_property("material_expression_editor_y", -1000)
    
    # Dissolve Tile
    dt = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    dt.set_editor_property("parameter_name", "Dissolve Tile")
    dt.set_editor_property("default_value", 0.08)
    dt.set_editor_property("material_expression_editor_x", -1200)
    dt.set_editor_property("material_expression_editor_y", -800)
    
    # WorldPosition
    wp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionWorldPosition)
    wp.set_editor_property("material_expression_editor_x", -1600)
    wp.set_editor_property("material_expression_editor_y", -800)
    
    # Multiply: WP * Tile
    mul_tile = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_tile.set_editor_property("material_expression_editor_x", -1000)
    mul_tile.set_editor_property("material_expression_editor_y", -700)
    
    # Noise (使用WP*Tile作为坐标)
    noise = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    noise.set_editor_property("material_expression_editor_x", -600)
    noise.set_editor_property("material_expression_editor_y", -700)
    
    # Subtract: Noise - DissolveAmount
    sub = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub.set_editor_property("material_expression_editor_x", -400)
    sub.set_editor_property("material_expression_editor_y", -600)
    
    # Add: Sub + DissolveEdge
    add_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionAdd)
    add_edge.set_editor_property("material_expression_editor_x", -200)
    add_edge.set_editor_property("material_expression_editor_y", -700)
    
    # SmoothStep: Min=add_edge, Max=sub, Value=sub (边缘检测)
    # SmoothStep(add_edge, sub, sub) gives edge mask
    ss = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSmoothStep)
    ss.set_editor_property("material_expression_editor_x", 0)
    ss.set_editor_property("material_expression_editor_y", -600)
    
    # Multiply: EdgeColor * GlowIntensity
    mul_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_glow.set_editor_property("material_expression_editor_x", -200)
    mul_glow.set_editor_property("material_expression_editor_y", -900)
    
    # Lerp: A=原Emissive, B=发光色, Alpha=SmoothStep
    lerp_e = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate)
    lerp_e.set_editor_property("material_expression_editor_x", 200)
    lerp_e.set_editor_property("material_expression_editor_y", -700)
    
    # OneMinus: 反转SmoothStep作为Opacity
    om = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionOneMinus)
    om.set_editor_property("material_expression_editor_x", 200)
    om.set_editor_property("material_expression_editor_y", -500)
    
    # ========= 连接节点 =========
    
    # WP -> MulTile.A
    unreal.MaterialEditingLibrary.connect_material_expressions(wp, "", mul_tile, "A")
    # Tile -> MulTile.B
    unreal.MaterialEditingLibrary.connect_material_expressions(dt, "", mul_tile, "B")
    # MulTile -> Noise.WorldPosition
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_tile, "", noise, "World Position")
    # Noise -> Sub.A
    unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", sub, "A")
    # DissolveAmount -> Sub.B
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", sub, "B")
    # Sub -> AddEdge.A
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", add_edge, "A")
    # DissolveEdge -> AddEdge.B
    unreal.MaterialEditingLibrary.connect_material_expressions(de, "", add_edge, "B")
    # AddEdge -> SmoothStep.Min
    unreal.MaterialEditingLibrary.connect_material_expressions(add_edge, "", ss, "Min")
    # Sub -> SmoothStep.Max  (用一个常数offset或者直接连)
    # 先用一个add节点增加DissolveEdge宽度来设置Max
    # 实际上，直接用Sub连接Max也是合理的
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", ss, "Max")
    # Sub -> SmoothStep.Value
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", ss, "Value")
    # EdgeColor -> MulGlow.A
    unreal.MaterialEditingLibrary.connect_material_expressions(ec, "", mul_glow, "A")
    # GlowIntensity -> MulGlow.B
    unreal.MaterialEditingLibrary.connect_material_expressions(gi, "", mul_glow, "B")
    # SmoothStep -> Lerp.Alpha
    unreal.MaterialEditingLibrary.connect_material_expressions(ss, "", lerp_e, "Alpha")
    # MulGlow -> Lerp.B
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_glow, "", lerp_e, "B")
    # SmoothStep -> OneMinus
    unreal.MaterialEditingLibrary.connect_material_expressions(ss, "", om, "None")
    
    # ========= 连接到材质属性 =========
    
    # 如果有原Emissive节点，连到Lerp.A
    if orig_emissive_node:
        unreal.MaterialEditingLibrary.connect_material_expressions(orig_emissive_node, "", lerp_e, "A")
    
    # Lerp -> Emissive Color
    unreal.MaterialEditingLibrary.connect_material_property(lerp_e, "", "emissive_color")
    # OneMinus -> Opacity
    unreal.MaterialEditingLibrary.connect_material_property(om, "", "opacity")
    
    r["all_connected"] = True
    
    # 编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["compiled"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset(mat_path, only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "ue5_build2.json"), "w") as f:
    json.dump(r, f, indent=2)
