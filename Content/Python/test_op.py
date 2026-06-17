import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    # 创建一个Constant=1.0直接连Opacity
    c1 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    c1.set_editor_property("r", 1.0)
    c1.set_editor_property("material_expression_editor_x", -600)
    c1.set_editor_property("material_expression_editor_y", 200)
    
    # 连接到Opacity
    unreal.MaterialEditingLibrary.connect_material_property(c1, "", unreal.MaterialProperty.MP_OPACITY)
    r["opacity_const1"] = True
    
    # 重新编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["recompiled"] = True

with open(os.path.join(os.environ["USERPROFILE"], "test_op.json"), "w") as f:
    json.dump(r, f, indent=2)
