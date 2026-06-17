import unreal, json, os

r = {}

# 重建整个材质 - 修复溶解逻辑
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"

# 删除重建
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    unreal.EditorAssetLibrary.delete_asset(mat_path)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
source = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source)

if not mat:
    r["error"] = "duplicate failed"
else:
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    
    # 获取原emissive节点
    orig_e = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["orig_emissive"] = orig_e.get_name() if orig_e else "None"
    
    # ========= 溶解逻辑修复 =========
    # 正确逻辑：
    # Noise值(0~1范围) 与 DissolveAmount 对比
    # 当 DissolveAmount=0: 所有噪声值 > 0 → opacity=1
    # 当 DissolveAmount=1: 所有噪声值 < 1 → opacity=0
    # 边缘：当 Noise ≈ DissolveAmount 时发光
    
    # 1. Dissolve Amount
    da = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    da.set_editor_property("parameter_name", "Dissolve Amount")
    da.set_editor_property("default_value", 0.0)
    da.set_editor_property("material_expression_editor_x", -600)
    da.set_editor_property("material_expression_editor_y", -600)
    
    # 2. Dissolve Edge Width
    de = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    de.set_editor_property("parameter_name", "Dissolve Edge")
    de.set_editor_property("default_value", 0.05)
    de.set_editor_property("material_expression_editor_x", -600)
    de.set_editor_property("material_expression_editor_y", -400)
    
    # 3. Dissolve Tile
    dt = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    dt.set_editor_property("parameter_name", "Dissolve Tile")
    dt.set_editor_property("default_value", 0.08)
    dt.set_editor_property("material_expression_editor_x", -1200)
    dt.set_editor_property("material_expression_editor_y", -800)
    
    # 4. Dissolve Edge Color
    ec = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
    ec.set_editor_property("parameter_name", "Dissolve Edge Color")
    ec.set_editor_property("default_value", unreal.LinearColor(0.3, 0.8, 0.2, 1.0))
    ec.set_editor_property("material_expression_editor_x", -400)
    ec.set_editor_property("material_expression_editor_y", -900)
    
    # 5. Dissolve Glow Intensity
    gi = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    gi.set_editor_property("parameter_name", "Dissolve Glow Intensity")
    gi.set_editor_property("default_value", 2.0)
    gi.set_editor_property("material_expression_editor_x", -600)
    gi.set_editor_property("material_expression_editor_y", -1000)
    
    # 6. WorldPosition
    wp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionWorldPosition)
    wp.set_editor_property("material_expression_editor_x", -1600)
    wp.set_editor_property("material_expression_editor_y", -800)
    
    # 7. Multiply: WP * Tile
    mul_tile = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_tile.set_editor_property("material_expression_editor_x", -1000)
    mul_tile.set_editor_property("material_expression_editor_y", -700)
    
    # 8. Noise (输出0~1范围)
    noise = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    noise.set_editor_property("material_expression_editor_x", -800)
    noise.set_editor_property("material_expression_editor_y", -700)
    
    # 9. Subtract: DissolveAmount - Noise (正值=溶解, 负值=可见)
    sub = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub.set_editor_property("material_expression_editor_x", -400)
    sub.set_editor_property("material_expression_editor_y", -600)
    
    # 10. Clamp (0~1): 将subtract结果截断到0~1 → 这就是opacity
    # 当 DA=0, Noise=0.5 → 0-0.5=-0.5 → clamp=0 → 但这不对
    # 
    # 重新思考：
    # opacity = Noise - DissolveAmount 的正值部分
    # 用 Saturate(Noise - DissolveAmount) 即可
    # 当 DA=0: Noise-0=Noise → saturate≈1 → 可见
    # 当 DA=1: Noise-1≤0 → saturate=0 → 不可见
    
    # 所以应该用: Subtract(A=Noise, B=DissolveAmount) → Saturate → Opacity
    # 不需要OneMinus！
    
    # 11. Saturate (clamp 0~1) 作为Opacity
    # UE没有Saturate节点，用Clamp
    clamp_op = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionClamp)
    clamp_op.set_editor_property("clamp_mode", unreal.ClampMode.CMODE_CLAMP)
    clamp_op.set_editor_property("material_expression_editor_x", -200)
    clamp_op.set_editor_property("material_expression_editor_y", -500)
    
    # 12. 边缘检测: Saturate(DissolveAmount - Noise) * Saturate(Noise - (DissolveAmount - Edge))
    # 简化: 边缘 = Saturate(Noise - (DissolveAmount - Edge)) - Saturate(Noise - DissolveAmount)
    # 或者: 边缘蒙版 = Saturate(1 - abs(Noise - DissolveAmount) / Edge)
    
    # 更简单: 用SmoothStep检测边缘
    # edge_mask = 1 - SmoothStep(DissolveAmount - Edge, DissolveAmount, Noise)
    # 即在 Noise ∈ [DA-Edge, DA] 区间内，edge_mask从1到0
    
    # Subtract2: DA - Edge
    sub2 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub2.set_editor_property("material_expression_editor_x", -400)
    sub2.set_editor_property("material_expression_editor_y", -800)
    
    # SmoothStep for edge mask
    ss_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSmoothStep)
    ss_edge.set_editor_property("material_expression_editor_x", -200)
    ss_edge.set_editor_property("material_expression_editor_y", -700)
    
    # OneMinus for edge mask (因为smoothstep从0到1, 我们需要1到0的过渡)
    om_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionOneMinus)
    om_edge.set_editor_property("material_expression_editor_x", 0)
    om_edge.set_editor_property("material_expression_editor_y", -700)
    
    # Multiply: EdgeColor * GlowIntensity
    mul_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_glow.set_editor_property("material_expression_editor_x", 0)
    mul_glow.set_editor_property("material_expression_editor_y", -900)
    
    # Multiply: edge_mask * (EdgeColor * Glow) 
    mul_final_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_final_glow.set_editor_property("material_expression_editor_x", 200)
    mul_final_glow.set_editor_property("material_expression_editor_y", -800)
    
    # Add: 原Emissive + 发光
    add_emissive = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionAdd)
    add_emissive.set_editor_property("material_expression_editor_x", 400)
    add_emissive.set_editor_property("material_expression_editor_y", -700)
    
    # ========= 连接 =========
    
    # WP -> MulTile.A
    unreal.MaterialEditingLibrary.connect_material_expressions(wp, "", mul_tile, "A")
    # Tile -> MulTile.B
    unreal.MaterialEditingLibrary.connect_material_expressions(dt, "", mul_tile, "B")
    # MulTile -> Noise.WorldPosition
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_tile, "", noise, "World Position")
    
    # === Opacity 通道 ===
    # Noise -> Sub.A (Noise - DissolveAmount)
    unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", sub, "A")
    # DissolveAmount -> Sub.B
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", sub, "B")
    # Sub -> Clamp (saturate)
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", clamp_op, "None")
    # Clamp -> Opacity
    unreal.MaterialEditingLibrary.connect_material_property(clamp_op, "", unreal.MaterialProperty.MP_OPACITY)
    
    # === 边缘发光 ===
    # DissolveAmount -> Sub2.A (DA - Edge)
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", sub2, "A")
    # DissolveEdge -> Sub2.B
    unreal.MaterialEditingLibrary.connect_material_expressions(de, "", sub2, "B")
    
    # Sub2 -> SmoothStep.Min (DA - Edge)
    unreal.MaterialEditingLibrary.connect_material_expressions(sub2, "", ss_edge, "Min")
    # DA -> SmoothStep.Max (DA)
    unreal.MaterialEditingLibrary.connect_material_expressions(da, "", ss_edge, "Max")
    # Noise -> SmoothStep.Value
    unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", ss_edge, "Value")
    
    # SmoothStep -> OneMinus (反转: 在边缘区域值=1)
    unreal.MaterialEditingLibrary.connect_material_expressions(ss_edge, "", om_edge, "")
    
    # EdgeColor -> MulGlow.A
    unreal.MaterialEditingLibrary.connect_material_expressions(ec, "", mul_glow, "A")
    # GlowIntensity -> MulGlow.B
    unreal.MaterialEditingLibrary.connect_material_expressions(gi, "", mul_glow, "B")
    
    # OneMinus -> MulFinalGlow.A (edge_mask * glow_color)
    unreal.MaterialEditingLibrary.connect_material_expressions(om_edge, "", mul_final_glow, "A")
    # MulGlow -> MulFinalGlow.B
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_glow, "", mul_final_glow, "B")
    
    # === Emissive: 原始 + 边缘发光 ===
    # 原Emissive -> Add.A
    if orig_e:
        unreal.MaterialEditingLibrary.connect_material_expressions(orig_e, "", add_emissive, "A")
    # MulFinalGlow -> Add.B
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_final_glow, "", add_emissive, "B")
    
    # Add -> Emissive Color
    unreal.MaterialEditingLibrary.connect_material_property(add_emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    
    r["all_connected"] = True
    
    # 编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["compiled"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset(mat_path, only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "fix_result.json"), "w") as f:
    json.dump(r, f, indent=2)
