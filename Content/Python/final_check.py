import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
if mat:
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["op_node"] = op.get_name() if op else "None"
    if op and "ScalarParameter" in op.get_class().get_name():
        r["param"] = str(op.get_editor_property("parameter_name"))
        r["val"] = op.get_editor_property("default_value")

with open(os.path.join(os.environ["USERPROFILE"], "final_check.json"), "w") as f:
    json.dump(r, f, indent=2)
