import unreal
import json
import os

r = {}

# 检查可用的位置设置方法
r["position_methods"] = [m for m in dir(unreal.MaterialEditingLibrary) if "position" in m.lower() or "node" in m.lower()]

# 检查Noise函数枚举
try:
    r["noise_enum"] = [x for x in dir(unreal.NoiseFunction) if not x.startswith('_')]
except Exception as e:
    r["noise_enum_err"] = str(e)

# 检查Clamp枚举
try:
    r["clamp_enum"] = [x for x in dir(unreal.ClampMode) if not x.startswith('_')]
except Exception as e:
    r["clamp_enum_err"] = str(e)

# 检查WorldPosition类型
try:
    r["wp_enum"] = [x for x in dir(unreal.WorldPositionType) if not x.startswith('_')]
except Exception as e:
    r["wp_enum_err"] = str(e)

# 检查MaterialExpressionScalarParameter的属性
try:
    sp = unreal.MaterialExpressionScalarParameter
    r["scalar_props"] = [x for x in dir(sp) if not x.startswith('_')][:30]
except Exception as e:
    r["scalar_err"] = str(e)

# 检查MaterialExpressionNoise的属性
try:
    n = unreal.MaterialExpressionNoise
    r["noise_props"] = [x for x in dir(n) if not x.startswith('_')][:30]
except Exception as e:
    r["noise_props_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_api.json"), "w") as f:
    json.dump(r, f, indent=2)
