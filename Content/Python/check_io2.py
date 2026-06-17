import unreal, json, os

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
r = {}

# 用已有的材质上的实例来查询输入输出名
# 先创建各种节点，然后查询
expr_types_to_create = [
    ("Multiply", unreal.MaterialExpressionMultiply),
    ("Add", unreal.MaterialExpressionAdd),
    ("Subtract", unreal.MaterialExpressionSubtract),
    ("Lerp", unreal.MaterialExpressionLinearInterpolate),
    ("OneMinus", unreal.MaterialExpressionOneMinus),
    ("Clamp", unreal.MaterialExpressionClamp),
    ("SmoothStep", unreal.MaterialExpressionSmoothStep),
    ("Noise", unreal.MaterialExpressionNoise),
    ("WorldPosition", unreal.MaterialExpressionWorldPosition),
]

for name, cls in expr_types_to_create:
    try:
        expr = unreal.MaterialEditingLibrary.create_material_expression(mat, cls)
        inputs = unreal.MaterialEditingLibrary.get_material_expression_input_names(expr)
        r[name] = {"inputs": [str(x) for x in inputs]}
    except Exception as e:
        r[name] = {"err": str(e)}

# 也获取connect_material_property的签名
try:
    r["connect_prop_sig"] = str(unreal.MaterialEditingLibrary.connect_material_property.__doc__[:500] if hasattr(unreal.MaterialEditingLibrary.connect_material_property, '__doc__') and unreal.MaterialEditingLibrary.connect_material_property.__doc__ else "no doc")
except:
    r["connect_prop_sig"] = "failed"

with open(os.path.join(os.environ["USERPROFILE"], "ue5_io2.json"), "w") as f:
    json.dump(r, f, indent=2)
