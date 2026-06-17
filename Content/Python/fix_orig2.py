import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
if mat:
    # 获取Opacity的输入节点
    op_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    if op_node:
        r["op_node_name"] = op_node.get_name()
        r["op_class"] = op_node.get_class().get_name()
        
        # 尝试获取参数名
        try:
            r["param_name"] = str(op_node.get_editor_property("parameter_name"))
        except: pass
        try:
            r["default_val"] = op_node.get_editor_property("default_value")
        except: pass
        
        # 尝试删除这个表达式
        try:
            unreal.MaterialEditingLibrary.delete_material_expression(mat, op_node)
            r["deleted"] = True
        except Exception as e:
            r["delete_err"] = str(e)
        
        # 尝试用disconnect方式
        try:
            # 重新连接一个空的Constant=1.0
            c1 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
            c1.set_editor_property("r", 1.0)
            unreal.MaterialEditingLibrary.connect_material_property(c1, "", unreal.MaterialProperty.MP_OPACITY)
            r["override_with_1"] = True
        except Exception as e:
            r["override_err"] = str(e)
        
        # 重新编译
        unreal.MaterialEditingLibrary.recompile_material(mat)
        r["recompiled"] = True
        
        # 保存
        unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS", only_if_is_dirty=False)
        r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "fix_orig2.json"), "w") as f:
    json.dump(r, f, indent=2)
