import unreal, json, os

r = {}
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
if mat:
    r["blend"] = str(mat.get_editor_property("blend_mode"))
    r["shading"] = str(mat.get_editor_property("shading_model"))
    
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["opacity"] = op.get_name() if op else "None (正确-无连接)"

with open(os.path.join(os.environ["USERPROFILE"], "verify_fix.json"), "w") as f:
    json.dump(r, f, indent=2)
