import unreal, json, os

r = {}

# 设置父材质
mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
parent = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")

if mi and parent:
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    r["parent_set"] = True
    r["parent_name"] = parent.get_path_name()
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve", only_if_is_dirty=False)
    r["saved"] = True
else:
    r["error"] = "mi or parent not found"

with open(os.path.join(os.environ["USERPROFILE"], "r2.json"), "w") as f:
    json.dump(r, f, indent=2)
