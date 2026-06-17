import unreal, json, os

r = {}
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if not mat:
    r["error"] = "not found"
else:
    r["found"] = True
    r["blend"] = str(mat.get_editor_property("blend_mode"))
    r["num_expr"] = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    
with open(os.path.join(os.environ["USERPROFILE"], "check.json"), "w") as f:
    json.dump(r, f, indent=2)
