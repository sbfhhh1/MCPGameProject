import unreal, json, os

r = {}

# 更新MI_YZL_JadeDissolve: 设置DissolveProgress=0
mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
if mi:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "DissolveProgress", 0.0)
    r["dp_set"] = True
    
    # 应用到YZL
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        if a.get_name() == "part_00000001_0":
            smc_list = a.get_components_by_class(unreal.StaticMeshComponent)
            if smc_list:
                smc = smc_list[0]
                smc.set_material(0, mi)
                r["applied"] = True
            break
    
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve", only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "apply_fix.json"), "w") as f:
    json.dump(r, f, indent=2)
