import unreal, json, os

r = {}

# 1. 创建材质实例 MI_YZL_JadeDissolve
mi_path = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve"

# 检查是否已存在
if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
    unreal.EditorAssetLibrary.delete_asset(mi_path)
    r["deleted_old_mi"] = True

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mi = asset_tools.create_asset("MI_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", unreal.MaterialInstanceConstant, None)

if mi:
    r["mi_created"] = mi.get_path_name()
    
    # 设置父材质
    parent = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    r["parent_set"] = True
    
    # 更新材质实例
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    
    # 保存
    unreal.EditorAssetLibrary.save_asset(mi_path, only_if_is_dirty=False)
    r["mi_saved"] = True
    
    # 2. 替换YZL的材质
    # 获取YZL Actor
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    yzl_actor = None
    for a in actors:
        if "part_00000001_0" in a.get_name() or a.get_name() == "YZL":
            yzl_actor = a
            break
    
    if yzl_actor:
        r["yzl_found"] = yzl_actor.get_name()
        # 获取StaticMeshComponent
        comps = yzl_actor.get_components_by_class(unreal.StaticMeshComponent)
        if comps:
            r["num_comps"] = len(comps)
            smc = comps[0]
            # 设置材质
            num_mats = smc.get_num_materials()
            r["num_mats"] = num_mats
            smc.set_material(0, mi)
            r["mat_set"] = True
        else:
            r["no_comps"] = True
    else:
        # 尝试其他方式查找
        for a in actors:
            n = a.get_name()
            if "YZL" in n or "yzl" in n:
                r["found_actor"] = n
except Exception as e:
    r["error"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_mi_result.json"), "w") as f:
    json.dump(r, f, indent=2)
