import unreal, json, os

r = {}
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    # 标记dirty强制重新编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["recompiled"] = True

with open(os.path.join(os.environ["USERPROFILE"], "recomp.json"), "w") as f:
    json.dump(r, f, indent=2)
