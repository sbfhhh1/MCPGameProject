import unreal, json, os

r = {}

# 查找YZL
actors = unreal.EditorLevelLibrary.get_all_level_actors()
yzl = None
for a in actors:
    if a.get_name() == "part_00000001_0":
        yzl = a
        break

if yzl:
    r["found"] = yzl.get_name()
    r["class"] = yzl.get_class().get_name()
    
    # 获取StaticMeshComponent
    smc_list = yzl.get_components_by_class(unreal.StaticMeshComponent)
    r["num_smc"] = len(smc_list)
    
    if smc_list:
        smc = smc_list[0]
        r["smc_name"] = smc.get_name()
        r["num_mats"] = smc.get_num_materials()
        
        # 获取当前材质
        for i in range(smc.get_num_materials()):
            m = smc.get_material(i)
            r[f"mat_{i}"] = m.get_path_name() if m else "None"
        
        # 替换材质slot 0
        mi = unreal.load_asset("/Game/TransformationVFS/SM2SM/jude/MI_YZL_JadeDissolve")
        if not mi:
            # 可能路径错了
            mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
        
        if mi:
            smc.set_material(0, mi)
            r["mat_replaced"] = True
            r["new_mat"] = mi.get_path_name()
        else:
            r["mi_not_found"] = True
    else:
        r["no_smc"] = True
else:
    r["not_found"] = True

with open(os.path.join(os.environ["USERPROFILE"], "r4.json"), "w") as f:
    json.dump(r, f, indent=2)
