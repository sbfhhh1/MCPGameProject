import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if not mat:
    r["error"] = "not found"
else:
    # 用Saturate节点替代Clamp，和M_Burst_JadeDissolve一样
    sat = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSaturate)
    sat.set_editor_property("material_expression_editor_x", -800)
    sat.set_editor_property("material_expression_editor_y", -300)
    
    # 找到DissolveAmount2的Subtract输出节点（连接到旧Clamp的那个）
    # 我们需要: Noise -> Subtract(A=Noise, B=DA2) -> Saturate -> Opacity
    # 但之前的Subtract连到了Clamp_0，现在需要重新连到Saturate
    
    # 先把Subtract连接到Saturate
    # 但我们不知道Subtract节点的引用...
    # 用get_material_property_input_node反推
    
    # 当前的Opacity连到Clamp_0
    clamp_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["current_op"] = clamp_node.get_name() if clamp_node else "None"
    
    # Clamp_0的输入应该连着Subtract
    # 我们需要把Saturate连在Subtract和Opacity之间
    
    # 最简方案：把Clamp_0的输入断开，连到Saturate，Saturate连到Opacity
    # 但API没有"get input of node"的方法
    
    # 替代方案：创建一组全新的正确节点
    # 用和M_Burst_JadeDissolve一样的逻辑
    
    # 先创建新的参数节点（用一个统一的名字DissolveAmount）
    # 但已有DissolveAmount2和Dissolve Amount参数
    
    # 最彻底的做法：重新连接所有需要的溶解节点
    # 创建: Noise2 -> Subtract2(Noise-DA) -> Saturate -> Opacity
    
    da_final = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    da_final.set_editor_property("parameter_name", "DissolveProgress")
    da_final.set_editor_property("default_value", 0.0)
    da_final.set_editor_property("material_expression_editor_x", -1600)
    da_final.set_editor_property("material_expression_editor_y", 0)
    
    noise3 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
    noise3.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    noise3.set_editor_property("material_expression_editor_x", -1400)
    noise3.set_editor_property("material_expression_editor_y", 0)
    
    sub3 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    sub3.set_editor_property("material_expression_editor_x", -1200)
    sub3.set_editor_property("material_expression_editor_y", 0)
    
    sat2 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSaturate)
    sat2.set_editor_property("material_expression_editor_x", -1000)
    sat2.set_editor_property("material_expression_editor_y", 0)
    
    # 连接
    # Noise -> Sub.A
    unreal.MaterialEditingLibrary.connect_material_expressions(noise3, "", sub3, "A")
    # DissolveProgress -> Sub.B
    unreal.MaterialEditingLibrary.connect_material_expressions(da_final, "", sub3, "B")
    # Sub -> Saturate
    unreal.MaterialEditingLibrary.connect_material_expressions(sub3, "", sat2, "")
    # Saturate -> Opacity
    unreal.MaterialEditingLibrary.connect_material_property(sat2, "", unreal.MaterialProperty.MP_OPACITY)
    
    r["new_logic_connected"] = True
    
    # 重新编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["recompiled"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve", only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "fix3.json"), "w") as f:
    json.dump(r, f, indent=2)
