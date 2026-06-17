import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
if mat:
    # 遍历表达式找到ScalarParameter_90
    num = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    r["num"] = num
    
    target = None
    for i in range(num):
        expr = unreal.MaterialEditingLibrary.get_material_expression(mat, i)
        if expr and expr.get_name() == "MaterialExpressionScalarParameter_90":
            target = expr
            r["found"] = i
            r["param_name"] = str(expr.get_editor_property("parameter_name"))
            r["default_val"] = expr.get_editor_property("default_value")
            break
    
    if not target:
        r["not_found"] = True

with open(os.path.join(os.environ["USERPROFILE"], "find_sp90.json"), "w") as f:
    json.dump(r, f, indent=2)
