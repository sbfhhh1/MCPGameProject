import unreal, json, os
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve")
r = {}
if mat:
    r["name"] = mat.get_name()
    r["num_expr"] = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    sn = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)
    r["scalars"] = [{"n": str(x), "v": unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(mat, x)} for x in sn]
    vn = unreal.MaterialEditingLibrary.get_vector_parameter_names(mat)
    r["vectors"] = [{"n": str(x), "v": str(unreal.MaterialEditingLibrary.get_material_default_vector_parameter_value(mat, x))} for x in vn]
    tn = unreal.MaterialEditingLibrary.get_texture_parameter_names(mat)
    r["textures"] = [{"n": str(x), "v": unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(mat, x).get_path_name() if unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(mat, x) else "None"} for x in tn]
else:
    r["error"] = "not found"
with open(os.path.join(os.environ["USERPROFILE"], "ue5_dissolve.json"), "w") as f:
    json.dump(r, f, indent=2)
