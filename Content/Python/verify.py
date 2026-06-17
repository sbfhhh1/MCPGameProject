import unreal, json, os

r = {}

# 检查当前Opacity连接
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["opacity_node"] = op.get_name() if op else "None"
    r["opacity_class"] = op.get_class().get_name() if op else "None"

# 更新材质实例 - 设置DissolveAmount2=0
mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
if mi:
    # 设置DissolveAmount2 = 0（完全可见）
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "DissolveAmount2", 0.0)
        r["mi_da2_set"] = True
    except Exception as e:
        r["mi_da2_err"] = str(e)
    
    # 确认旧参数也保留
    da1 = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Dissolve Amount")
    r["mi_da1"] = da1
    da2 = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "DissolveAmount2")
    r["mi_da2"] = da2
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve", only_if_is_dirty=False)
    r["mi_saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "verify.json"), "w") as f:
    json.dump(r, f, indent=2)
