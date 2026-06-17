import unreal, json, os

r = {}

# 先恢复原始材质确认模型可见
actors = unreal.EditorLevelLibrary.get_all_level_actors()
yzl = None
for a in actors:
    if a.get_name() == "part_00000001_0":
        yzl = a
        break

if yzl:
    smc_list = yzl.get_components_by_class(unreal.StaticMeshComponent)
    if smc_list:
        smc = smc_list[0]
        # 恢复原始材质
        orig_mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
        if orig_mi:
            smc.set_material(0, orig_mi)
            r["restored"] = True
            r["mat"] = orig_mi.get_path_name()
        else:
            r["orig_not_found"] = True

with open(os.path.join(os.environ["USERPROFILE"], "restore.json"), "w") as f:
    json.dump(r, f, indent=2)
