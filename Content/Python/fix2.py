import unreal, json, os

r = {}
mat = unreal.load_asset("/Game/TransformationVFS/SM2SM/jude/M_YZL_JadeDissolve")
if not mat:
    mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")

if not mat:
    r["error"] = "not found"
else:
    # 先断开所有旧的溶解连接
    # 清除Opacity连接 - 用delete方式
    # 策略：删除所有我们添加的节点，重新添加正确逻辑
    
    # 删除材质中所有表达式，然后重新添加
    # 但这会删除原始节点...
    
    # 更好的方案：直接删除我们添加的节点
    # 之前添加的节点名是自动生成的，不确定
    # 让我列出所有节点名
    num = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    r["num_expr"] = num
    
    # 尝试用delete_all_material_expressions删除全部然后重新添加
    # 不行，原始玉石节点也会被删
    
    # 最简单：直接在现有基础上修改连接
    # 1. 重新连接Opacity到正确的节点
    
    # 先创建需要的修复节点
    # Clamped Saturate: Noise - DissolveAmount → Clamp(0,1) → Opacity
    
    # 创建 Subtract: Noise - DissolveAmount
    new_sub = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSubtract)
    new_sub.set_editor_property("material_expression_editor_x", -1200)
    new_sub.set_editor_property("material_expression_editor_y", -300)
    
    # 创建 Clamp for opacity
    new_clamp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionClamp)
    new_clamp.set_editor_property("clamp_mode", unreal.ClampMode.CMODE_CLAMP)
    new_clamp.set_editor_property("material_expression_editor_x", -1000)
    new_clamp.set_editor_property("material_expression_editor_y", -300)
    
    r["fix_nodes_created"] = True
    
    # 需要找到之前的Noise和DissolveAmount节点
    # 通过参数名查找
    # 用scalar参数接口来找
    # 不能直接遍历，让我用get_scalar_parameter_names来验证
    
    # 另一种方法：直接创建新的Noise和参数节点
    # 因为旧节点连接可能有问题
    
    new_da = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    new_da.set_editor_property("parameter_name", "DissolveAmount2")
    new_da.set_editor_property("default_value", 0.0)
    new_da.set_editor_property("material_expression_editor_x", -1600)
    new_da.set_editor_property("material_expression_editor_y", -300)
    
    new_noise = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionNoise)
    new_noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    new_noise.set_editor_property("material_expression_editor_x", -1400)
    new_noise.set_editor_property("material_expression_editor_y", -300)
    
    # 连接
    # Noise -> Sub.A
    unreal.MaterialEditingLibrary.connect_material_expressions(new_noise, "", new_sub, "A")
    # DissolveAmount2 -> Sub.B
    unreal.MaterialEditingLibrary.connect_material_expressions(new_da, "", new_sub, "B")
    # Sub -> Clamp
    unreal.MaterialEditingLibrary.connect_material_expressions(new_sub, "", new_clamp, "None")
    # Clamp -> Opacity (覆盖旧连接)
    unreal.MaterialEditingLibrary.connect_material_property(new_clamp, "", unreal.MaterialProperty.MP_OPACITY)
    
    r["fix_connected"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve", only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "fix2.json"), "w") as f:
    json.dump(r, f, indent=2)
