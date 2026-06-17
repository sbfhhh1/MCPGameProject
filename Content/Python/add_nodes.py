import unreal
import json
import os

mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"
mat = unreal.load_asset(mat_path)
r = {"path": mat_path}

if not mat:
    r["error"] = "not found"
else:
    # 1. 修改 Blend Mode 为 Translucent
    try:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        r["blend_mode"] = "set_translucent"
    except Exception as e:
        r["blend_mode_err"] = str(e)
    
    # 2. 添加标量参数节点
    try:
        # Dissolve Amount
        dissolve_amount = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
        dissolve_amount.set_editor_property("parameter_name", "Dissolve Amount")
        dissolve_amount.set_editor_property("default_value", 0.0)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, dissolve_amount, -800, -600)
        r["dissolve_amount"] = "created"
    except Exception as e:
        r["dissolve_amount_err"] = str(e)
    
    try:
        # Dissolve Edge
        dissolve_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
        dissolve_edge.set_editor_property("parameter_name", "Dissolve Edge")
        dissolve_edge.set_editor_property("default_value", 0.05)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, dissolve_edge, -800, -400)
        r["dissolve_edge"] = "created"
    except Exception as e:
        r["dissolve_edge_err"] = str(e)
    
    try:
        # Dissolve Contrast
        dissolve_contrast = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
        dissolve_contrast.set_editor_property("parameter_name", "Dissolve Contrast")
        dissolve_contrast.set_editor_property("default_value", 3.0)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, dissolve_contrast, -800, -200)
        r["dissolve_contrast"] = "created"
    except Exception as e:
        r["dissolve_contrast_err"] = str(e)
    
    try:
        # Dissolve Tile (噪声平铺)
        dissolve_tile = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
        dissolve_tile.set_editor_property("parameter_name", "Dissolve Tile")
        dissolve_tile.set_editor_property("default_value", 0.08)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, dissolve_tile, -1200, -600)
        r["dissolve_tile"] = "created"
    except Exception as e:
        r["dissolve_tile_err"] = str(e)

    # 3. 创建噪声节点
    try:
        noise = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
        noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_Gradient)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, noise, -600, -600)
        r["noise"] = "created"
    except Exception as e:
        r["noise_err"] = str(e)
    
    # 4. 创建 World Position 节点用于噪声坐标
    try:
        wp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionWorldPosition)
        wp.set_editor_property("world_position_shader_offset", unreal.WorldPositionType.WPT_Absolute)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, wp, -1600, -600)
        r["world_pos"] = "created"
    except Exception as e:
        r["world_pos_err"] = str(e)
    
    # 5. 创建 Multiply 节点 (WP * Tile)
    try:
        mul_tile = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, mul_tile, -1000, -500)
        r["mul_tile"] = "created"
    except Exception as e:
        r["mul_tile_err"] = str(e)
    
    # 6. 创建 Subtract 节点 (Noise - DissolveAmount)
    try:
        sub = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, sub, -400, -500)
        r["subtract"] = "created"
    except Exception as e:
        r["subtract_err"] = str(e)
    
    # 7. 创建 Add 节点 (Subtract + DissolveEdge) 用于emissive边缘
    try:
        add_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionAdd)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, add_edge, -200, -700)
        r["add_edge"] = "created"
    except Exception as e:
        r["add_edge_err"] = str(e)
    
    # 8. 创建 Clamp 节点用于Opacity
    try:
        clamp_opacity = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionClamp)
        clamp_opacity.set_editor_property("clamp_mode", unreal.ClampMode.CMC_Clamp)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, clamp_opacity, -200, -400)
        r["clamp"] = "created"
    except Exception as e:
        r["clamp_err"] = str(e)
    
    # 9. 创建 SmoothStep 节点用于溶解边缘
    try:
        smoothstep = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSmoothStep)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, smoothstep, -200, -500)
        r["smoothstep"] = "created"
    except Exception as e:
        r["smoothstep_err"] = str(e)
    
    # 10. 创建向量参数 Dissolve Edge Color
    try:
        edge_color = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
        edge_color.set_editor_property("parameter_name", "Dissolve Edge Color")
        lc = unreal.LinearColor(0.3, 0.8, 0.2, 1.0)  # 翡翠绿色边缘
        edge_color.set_editor_property("default_value", lc)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, edge_color, -400, -900)
        r["edge_color"] = "created"
    except Exception as e:
        r["edge_color_err"] = str(e)
    
    # 11. 创建 Lerp 用于边缘发光
    try:
        lerp_emissive = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, lerp_emissive, 0, -700)
        r["lerp_emissive"] = "created"
    except Exception as e:
        r["lerp_emissive_err"] = str(e)
    
    # 12. 创建 Multiply 用于边缘发光强度
    try:
        mul_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, mul_glow, -400, -1000)
        r["mul_glow"] = "created"
    except Exception as e:
        r["mul_glow_err"] = str(e)
    
    # 13. ScalarParameter Dissolve Glow Intensity
    try:
        glow_intensity = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
        glow_intensity.set_editor_property("parameter_name", "Dissolve Glow Intensity")
        glow_intensity.set_editor_property("default_value", 2.0)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, glow_intensity, -600, -1000)
        r["glow_intensity"] = "created"
    except Exception as e:
        r["glow_intensity_err"] = str(e)
    
    # 14. 创建1-节点 (OneMinus) 用于反转边缘
    try:
        one_minus = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionOneMinus)
        unreal.MaterialEditingLibrary.set_material_expression_node_position(mat, one_minus, 0, -500)
        r["one_minus"] = "created"
    except Exception as e:
        r["one_minus_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_nodes_result.json"), "w") as f:
    json.dump(r, f, indent=2)
