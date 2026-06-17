import unreal
import json
import os

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
r = {"name": mat.get_name() if mat else "None"}

if mat:
    # scalar params
    try:
        sn = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)
        r["scalars"] = []
        for n in sn:
            v = unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(mat, n)
            r["scalars"].append({"n": str(n), "v": v})
    except Exception as e:
        r["s_err"] = str(e)
    
    # vector params
    try:
        vn = unreal.MaterialEditingLibrary.get_vector_parameter_names(mat)
        r["vectors"] = []
        for n in vn:
            v = unreal.MaterialEditingLibrary.get_material_default_vector_parameter_value(mat, n)
            r["vectors"].append({"n": str(n), "v": str(v)})
    except Exception as e:
        r["v_err"] = str(e)
    
    # texture params
    try:
        tn = unreal.MaterialEditingLibrary.get_texture_parameter_names(mat)
        r["textures"] = []
        for n in tn:
            v = unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(mat, n)
            r["textures"].append({"n": str(n), "v": v.get_path_name() if v else "None"})
    except Exception as e:
        r["t_err"] = str(e)
    
    # static switches
    try:
        wn = unreal.MaterialEditingLibrary.get_static_switch_parameter_names(mat)
        r["switches"] = []
        for n in wn:
            v = unreal.MaterialEditingLibrary.get_material_default_static_switch_parameter_value(mat, n)
            r["switches"].append({"n": str(n), "v": str(v)})
    except Exception as e:
        r["w_err"] = str(e)
    
    # num expressions
    try:
        r["num_expr"] = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    except Exception as e:
        r["ne_err"] = str(e)

out = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\lafa"), "ue5_mat_expr.json")
with open(out, "w") as f:
    json.dump(r, f, indent=2)
