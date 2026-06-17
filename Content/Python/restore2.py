import unreal, json, os

r = {}

# 还原YZL为原始材质
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if a.get_name() == "part_00000001_0":
        smc = a.get_components_by_class(unreal.StaticMeshComponent)[0]
        orig = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
        if orig:
            smc.set_material(0, orig)
            r["restored"] = True
            r["mat"] = orig.get_path_name()
        break

with open(os.path.join(os.environ["USERPROFILE"], "restore2.json"), "w") as f:
    json.dump(r, f, indent=2)
