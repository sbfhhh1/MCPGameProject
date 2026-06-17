import unreal, json, os

r = {}

ref = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_Burst_JadeDissolve")
if ref:
    r["blend"] = str(ref.get_editor_property("blend_mode"))
    r["shading"] = str(ref.get_editor_property("shading_model"))
    
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(ref, unreal.MaterialProperty.MP_OPACITY)
    r["op"] = op.get_name() if op else "None"
    r["op_class"] = op.get_class().get_name() if op else "None"
    
    em = unreal.MaterialEditingLibrary.get_material_property_input_node(ref, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r["em"] = em.get_name() if em else "None"

with open(os.path.join(os.environ["USERPROFILE"], "ref2.json"), "w") as f:
    json.dump(r, f, indent=2)
