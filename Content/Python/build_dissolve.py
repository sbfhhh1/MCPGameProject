import unreal
import json
import os

# 删除之前创建的错误材质
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"
mat = unreal.load_asset(mat_path)
r = {}

if mat:
    # 先删除这个材质，重新创建
    unreal.EditorAssetLibrary.delete_asset(mat_path)
    r["deleted"] = True
else:
    r["not_found"] = True

# 重新复制材质
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
source_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
source_asset = unreal.load_asset(source_path)

if source_asset:
    new_mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source_asset)
    if new_mat:
        r["recreated"] = new_mat.get_path_name()
        
        # 设置 Blend Mode 为 Translucent
        new_mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        r["blend_mode"] = "translucent"
        
        # ============ 创建节点 ============
        
        # 1. Dissolve Amount (ScalarParameter)
        da = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionScalarParameter)
        da.set_editor_property("parameter_name", "Dissolve Amount")
        da.set_editor_property("default_value", 0.0)
        da.set_editor_property("material_expression_editor_x", -800)
        da.set_editor_property("material_expression_editor_y", -600)
        
        # 2. Dissolve Edge (ScalarParameter)
        de = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionScalarParameter)
        de.set_editor_property("parameter_name", "Dissolve Edge")
        de.set_editor_property("default_value", 0.05)
        de.set_editor_property("material_expression_editor_x", -800)
        de.set_editor_property("material_expression_editor_y", -400)
        
        # 3. Dissolve Contrast (ScalarParameter) 
        dc = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionScalarParameter)
        dc.set_editor_property("parameter_name", "Dissolve Contrast")
        dc.set_editor_property("default_value", 3.0)
        dc.set_editor_property("material_expression_editor_x", -800)
        dc.set_editor_property("material_expression_editor_y", -200)
        
        # 4. Dissolve Tile (ScalarParameter)
        dt = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionScalarParameter)
        dt.set_editor_property("parameter_name", "Dissolve Tile")
        dt.set_editor_property("default_value", 0.08)
        dt.set_editor_property("material_expression_editor_x", -1200)
        dt.set_editor_property("material_expression_editor_y", -800)
        
        # 5. World Position
        wp = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionWorldPosition)
        wp.set_editor_property("material_expression_editor_x", -1600)
        wp.set_editor_property("material_expression_editor_y", -800)
        
        # 6. Multiply (WP * Tile)
        mul_tile = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionMultiply)
        mul_tile.set_editor_property("material_expression_editor_x", -1000)
        mul_tile.set_editor_property("material_expression_editor_y", -700)
        
        # 7. Noise
        noise = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionNoise)
        noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
        noise.set_editor_property("material_expression_editor_x", -600)
        noise.set_editor_property("material_expression_editor_y", -700)
        
        # 8. Subtract (Noise - DissolveAmount)
        sub = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionSubtract)
        sub.set_editor_property("material_expression_editor_x", -400)
        sub.set_editor_property("material_expression_editor_y", -600)
        
        # 9. Dissolve Edge Color (VectorParameter)
        ec = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionVectorParameter)
        ec.set_editor_property("parameter_name", "Dissolve Edge Color")
        lc = unreal.LinearColor(0.3, 0.8, 0.2, 1.0)
        ec.set_editor_property("default_value", lc)
        ec.set_editor_property("material_expression_editor_x", -400)
        ec.set_editor_property("material_expression_editor_y", -900)
        
        # 10. Dissolve Glow Intensity (ScalarParameter)
        gi = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionScalarParameter)
        gi.set_editor_property("parameter_name", "Dissolve Glow Intensity")
        gi.set_editor_property("default_value", 2.0)
        gi.set_editor_property("material_expression_editor_x", -600)
        gi.set_editor_property("material_expression_editor_y", -1000)
        
        # 11. Multiply (EdgeColor * GlowIntensity)
        mul_glow = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionMultiply)
        mul_glow.set_editor_property("material_expression_editor_x", -200)
        mul_glow.set_editor_property("material_expression_editor_y", -900)
        
        # 12. Add (Subtract + DissolveEdge)
        add_edge = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionAdd)
        add_edge.set_editor_property("material_expression_editor_x", -200)
        add_edge.set_editor_property("material_expression_editor_y", -700)
        
        # 13. SmoothStep (边缘过渡)
        ss = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionSmoothStep)
        ss.set_editor_property("material_expression_editor_x", 0)
        ss.set_editor_property("material_expression_editor_y", -600)
        
        # 14. Lerp (原始Emissive vs 边缘发光)
        lerp_e = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionLinearInterpolate)
        lerp_e.set_editor_property("material_expression_editor_x", 200)
        lerp_e.set_editor_property("material_expression_editor_y", -700)
        
        # 15. OneMinus (反转smoothstep作为opacity mask)
        om = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionOneMinus)
        om.set_editor_property("material_expression_editor_x", 200)
        om.set_editor_property("material_expression_editor_y", -500)
        
        # ============ 连接节点 ============
        
        # WP -> Multiply.A
        unreal.MaterialEditingLibrary.connect_material_expressions(wp, "", 0, mul_tile, 0)
        # Tile -> Multiply.B
        unreal.MaterialEditingLibrary.connect_material_expressions(dt, "", 0, mul_tile, 1)
        # Multiply -> Noise.Coordinates
        unreal.MaterialEditingLibrary.connect_material_expressions(mul_tile, "", 0, noise, 0)
        # Noise -> Subtract.A
        unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", 0, sub, 0)
        # DissolveAmount -> Subtract.B
        unreal.MaterialEditingLibrary.connect_material_expressions(da, "", 0, sub, 1)
        # Subtract -> SmoothStep.Value
        unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", 0, ss, 2)
        # Subtract -> Add.A
        unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", 0, add_edge, 0)
        # DissolveEdge -> Add.B
        unreal.MaterialEditingLibrary.connect_material_expressions(de, "", 0, add_edge, 1)
        # Add -> SmoothStep.Min (edge)
        unreal.MaterialEditingLibrary.connect_material_expressions(add_edge, "", 0, ss, 0)
        # Subtract -> SmoothStep.Max (subtract+contrast range)
        # Actually smoothstep needs: min, max, value
        # Let's use a simpler approach: subtract -> smoothstep.value, with constants for min/max
        
        # EdgeColor -> Multiply_glow.A
        unreal.MaterialEditingLibrary.connect_material_expressions(ec, "", 0, mul_glow, 0)
        # GlowIntensity -> Multiply_glow.B
        unreal.MaterialEditingLibrary.connect_material_expressions(gi, "", 0, mul_glow, 1)
        
        # SmoothStep -> Lerp.Alpha
        unreal.MaterialEditingLibrary.connect_material_expressions(ss, "", 0, lerp_e, 2)
        # Mul_glow -> Lerp.B (edge glow when alpha=1)
        unreal.MaterialEditingLibrary.connect_material_expressions(mul_glow, "", 0, lerp_e, 1)
        
        # SmoothStep -> OneMinus (for opacity)
        unreal.MaterialEditingLibrary.connect_material_expressions(ss, "", 0, om, 0)
        
        # 连接到材质属性
        # OneMinus -> Opacity
        unreal.MaterialEditingLibrary.connect_material_property(om, "", 0, "opacity")
        # Lerp -> Emissive Color
        unreal.MaterialEditingLibrary.connect_material_property(lerp_e, "", 0, "emissive_color")
        
        r["nodes_created"] = True
        r["connections_made"] = True
        
        # 编译材质
        unreal.MaterialEditingLibrary.recompile_material(new_mat)
        r["compiled"] = True
        
        # 保存
        unreal.EditorAssetLibrary.save_asset(mat_path, only_if_is_dirty=False)
        r["saved"] = True
    else:
        r["duplicate_failed"] = True
else:
    r["source_not_found"] = True

with open(os.path.join(os.environ["USERPROFILE"], "ue5_build_result.json"), "w") as f:
    json.dump(r, f, indent=2)
