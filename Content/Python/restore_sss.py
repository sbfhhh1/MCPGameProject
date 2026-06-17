import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZZ_ProceduralJade_SSS")
if not mat:
    mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")

if mat:
    r["name"] = mat.get_name()
    
    # 检查Subsurface相关通道
    # MP_SUBSURFACE_COLOR 和 MP_OPACITY 在Opaque模式下控制SSS
    sc = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    r["subsurface_color_node"] = sc.get_name() if sc else "None"
    
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["opacity_node"] = op.get_name() if op else "None"
    
    # 在Opaque+Subsurface模式下，Opacity通道实际控制SSS Amount
    # 所以原来SSS Amount连到Opacity其实是正确的！
    # 只是值可能被改了
    
    r["insight"] = "In Opaque+Subsurface mode, Opacity pin controls SSS opacity/amount. SSS Amount connected to Opacity was CORRECT."
    
    # 需要把SSS Amount参数重新创建并连回Opacity
    sss = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    sss.set_editor_property("parameter_name", "SSS Amount")
    sss.set_editor_property("default_value", 0.35874998569488525)
    
    # 连到Opacity（在Subsurface模式下这是正确的）
    unreal.MaterialEditingLibrary.connect_material_property(sss, "", unreal.MaterialProperty.MP_OPACITY)
    r["sss_restored"] = True
    
    # 删除多余的Constant=1.0
    const_node = op  # 这是之前创建的Constant
    if const_node and "Constant" in const_node.get_class().get_name():
        unreal.MaterialEditingLibrary.delete_material_expression(mat, const_node)
        r["const_deleted"] = True
    
    # 重新编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["recompiled"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS", only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "restore_sss.json"), "w") as f:
    json.dump(r, f, indent=2)
