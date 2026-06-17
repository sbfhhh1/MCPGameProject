import unreal, json, os

r = {}

mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_Burst_Jade_YZL")
if mi:
    r["name"] = mi.get_name()
    r["class"] = mi.get_class().get_name()
    try:
        p = mi.get_editor_property("parent")
        r["parent"] = p.get_path_name() if p else "None"
    except: r["parent_err"] = True
    
    # 获取Dissolve Amount值
    try:
        da = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Dissolve Amount")
        r["dissolve_amount"] = da
    except: pass
else:
    r["not_found"] = True

with open(os.path.join(os.environ["USERPROFILE"], "mi_burst.json"), "w") as f:
    json.dump(r, f, indent=2)
