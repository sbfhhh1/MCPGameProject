import unreal, json, os

r = {}

# 验证MI_YZL_JadeDissolve的参数
mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
if mi:
    r["name"] = mi.get_name()
    r["class"] = mi.get_class().get_name()
    
    # 获取父材质
    parent = unreal.MaterialEditingLibrary.get_material_instance_parent(mi) if hasattr(unreal.MaterialEditingLibrary, 'get_material_instance_parent') else None
    # 使用get_editor_property
    try:
        p = mi.get_editor_property("parent")
        r["parent"] = p.get_path_name() if p else "None"
    except: pass
    
    # 获取标量参数值
    try:
        da = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Dissolve Amount")
        r["dissolve_amount"] = da
    except Exception as e:
        r["da_err"] = str(e)
    
    try:
        de = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Dissolve Edge")
        r["dissolve_edge"] = de
    except Exception as e:
        r["de_err"] = str(e)
    
    # 也获取一些原始玉石参数确保继承
    try:
        sss = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "SSS Amount")
        r["sss_amount"] = sss
    except Exception as e:
        r["sss_err"] = str(e)
    
    # 保存关卡
    try:
        unreal.EditorLevelLibrary.save_current_level()
        r["level_saved"] = True
    except Exception as e:
        r["save_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "r5.json"), "w") as f:
    json.dump(r, f, indent=2)
