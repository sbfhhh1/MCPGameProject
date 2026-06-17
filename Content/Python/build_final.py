import unreal, json, os

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
r = {}

if not mat:
    r["error"] = "not found"
else:
    # 获取原emissive连接
    orig_e = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["orig_emissive"] = orig_e.get_name() if orig_e else "None"
    
    # ========= 创建所有节点 =========
    
    da = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    da.set_editor_property("parameter_name", "Dissolve Amount")
    da.set_editor_property("default_value", 0.0)
    da.set_editor_property("material_expression_editor_x", -800)
    da.set_editor_property("material_expression_editor_y", -600)
    
    de = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    de.set_editor_property("parameter_name", "Dissolve Edge")
    de.set_editor_property("default_value", 0.05)
    de.set_editor_property("material_expression_editor_x", -800)
    de.set_editor_property("material_expression_editor_y", -400)
    
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
    
    dt = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    dt.set_editor_property("parameter_name", "Dissolve Tile")
    dt.set_editor_property("default_value", 0.08)
    dt.set_editor_property("material_expression_editor_x", -1200)
    dt.set_editor_property("material_expression_editor_y", -800)
    
    wp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionWorldPosition)
    wp.set_editor_property("material_expression_editor_x", -1600)
    wp.set_editor_property("material_expression_editor_y", -800)
    
    mul_tile = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_tile.set_editor_property("material_expression_editor_x", -1000)
    mul_tile.set_editor_property("material_expression_editor_y", -700)
    
    noise = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    noise.set_editor_property("material_expression_editor_x", -600)
    noise.set_editor_property("material_expression_editor_y", -700)
    
    sub = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub.set_editor_property("material_expression_editor_x", -400)
    sub.set_editor_property("material_expression_editor_y", -600)
    
    add_edge = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionAdd)
    add_edge.set_editor_property("material_expression_editor_x", -200)
    add_edge.set_editor_property("material_expression_editor_y", -700)
    
    ss = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSmoothStep)
    ss.set_editor_property("material_expression_editor_x", 0)
    ss.set_editor_property("material_expression_editor_y", -600)
    
    mul_glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul_glow.set_editor_property("material_expression_editor_x", -200)
    mul_glow.set_editor_property("material_expression_editor_y", -900)
    
    lerp_e = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate)
    lerp_e.set_editor_property("material_expression_editor_x", 200)
    lerp_e.set_editor_property("material_expression_editor_y", -700)
    
    om = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionOneMinus)
    om.set_editor_property("material_expression_editor_x", 200)
    om.set_editor_property("material_expression_editor_y", -500)
    
    r["nodes_created"] = True
    
    # ========= 连接节点 =========
    
    # WP -> MulTile.A
    c1 = unreal.MaterialEditingLibrary.connect_material_expressions(wp, "", mul_tile, "A")
    r["c1_wp_mul"] = c1
    # Tile -> MulTile.B
    c2 = unreal.MaterialEditingLibrary.connect_material_expressions(dt, "", mul_tile, "B")
    r["c2_tile_mul"] = c2
    # MulTile -> Noise.WorldPosition
    c3 = unreal.MaterialEditingLibrary.connect_material_expressions(mul_tile, "", noise, "World Position")
    r["c3_mul_noise"] = c3
    # Noise -> Sub.A
    c4 = unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", sub, "A")
    r["c4_noise_sub"] = c4
    # DissolveAmount -> Sub.B
    c5 = unreal.MaterialEditingLibrary.connect_material_expressions(da, "", sub, "B")
    r["c5_da_sub"] = c5
    # Sub -> AddEdge.A
    c6 = unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", add_edge, "A")
    r["c6_sub_add"] = c6
    # DissolveEdge -> AddEdge.B
    c7 = unreal.MaterialEditingLibrary.connect_material_expressions(de, "", add_edge, "B")
    r["c7_de_add"] = c7
    # AddEdge -> SmoothStep.Min
    c8 = unreal.MaterialEditingLibrary.connect_material_expressions(add_edge, "", ss, "Min")
    r["c8_add_ss_min"] = c8
    # Sub -> SmoothStep.Max
    c9 = unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", ss, "Max")
    r["c9_sub_ss_max"] = c9
    # Sub -> SmoothStep.Value
    c10 = unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", ss, "Value")
    r["c10_sub_ss_val"] = c10
    # EdgeColor -> MulGlow.A
    c11 = unreal.MaterialEditingLibrary.connect_material_expressions(ec, "", mul_glow, "A")
    r["c11_ec_mul"] = c11
    # GlowIntensity -> MulGlow.B
    c12 = unreal.MaterialEditingLibrary.connect_material_expressions(gi, "", mul_glow, "B")
    r["c12_gi_mul"] = c12
    # SmoothStep -> Lerp.Alpha
    c13 = unreal.MaterialEditingLibrary.connect_material_expressions(ss, "", lerp_e, "Alpha")
    r["c13_ss_lerp"] = c13
    # MulGlow -> Lerp.B
    c14 = unreal.MaterialEditingLibrary.connect_material_expressions(mul_glow, "", lerp_e, "B")
    r["c14_mul_lerp"] = c14
    # SmoothStep -> OneMinus (空字符串输入)
    c15 = unreal.MaterialEditingLibrary.connect_material_expressions(ss, "", om, "")
    r["c15_ss_om"] = c15
    
    # 原emissive -> Lerp.A
    if orig_e:
        c16 = unreal.MaterialEditingLibrary.connect_material_expressions(orig_e, "", lerp_e, "A")
        r["c16_orig_lerp"] = c16
    
    # ========= 连接材质属性 =========
    
    # Lerp -> Emissive Color
    cp1 = unreal.MaterialEditingLibrary.connect_material_property(lerp_e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["cp1_emissive"] = cp1
    # OneMinus -> Opacity
    cp2 = unreal.MaterialEditingLibrary.connect_material_property(om, "", unreal.MaterialProperty.MP_OPACITY)
    r["cp2_opacity"] = cp2
    
    r["all_connected"] = True
    
    # 编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["compiled"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve", only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "ue5_final.json"), "w") as f:
    json.dump(r, f, indent=2)
