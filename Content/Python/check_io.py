import unreal, json, os

# 获取常用表达式的输入输出名
r = {}

expr_types = [
    ("Multiply", unreal.MaterialExpressionMultiply),
    ("Add", unreal.MaterialExpressionAdd),
    ("Subtract", unreal.MaterialExpressionSubtract),
    ("LinearInterpolate", unreal.MaterialExpressionLinearInterpolate),
    ("OneMinus", unreal.MaterialExpressionOneMinus),
    ("Clamp", unreal.MaterialExpressionClamp),
    ("SmoothStep", unreal.MaterialExpressionSmoothStep),
    ("Noise", unreal.MaterialExpressionNoise),
    ("WorldPosition", unreal.MaterialExpressionWorldPosition),
    ("ScalarParameter", unreal.MaterialExpressionScalarParameter),
    ("VectorParameter", unreal.MaterialExpressionVectorParameter),
    ("Time", unreal.MaterialExpressionTime),
    ("Panner", unreal.MaterialExpressionPanner),
]

for name, cls in expr_types:
    try:
        inputs = unreal.MaterialEditingLibrary.get_material_expression_input_names(cls)
        outputs = unreal.MaterialEditingLibrary.get_material_expression_input_names(cls)
        r[name] = {"inputs": [str(x) for x in inputs], "output_names_method": [str(x) for x in outputs]}
    except Exception as e:
        r[name] = {"err": str(e)}

# 也获取输出名
for name, cls in expr_types:
    try:
        output_names = unreal.MaterialEditingLibrary.get_inputs_for_material_expression(cls)
        r[name + "_outputs"] = [str(x) for x in output_names] if output_names else "None"
    except Exception as e:
        r[name + "_out_err"] = str(e)

# 检查get_material_expression_input_types
for name, cls in expr_types:
    try:
        types = unreal.MaterialEditingLibrary.get_material_expression_input_types(cls)
        r[name + "_types"] = [str(x) for x in types] if types else "None"
    except Exception as e:
        r[name + "_types_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_io.json"), "w") as f:
    json.dump(r, f, indent=2)
