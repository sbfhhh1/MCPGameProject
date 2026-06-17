import unreal, json, os

# 检查MaterialProperty枚举
r = {}
try:
    r["mat_props"] = [x for x in dir(unreal.MaterialProperty) if not x.startswith('_')]
except Exception as e:
    r["err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_enum.json"), "w") as f:
    json.dump(r, f, indent=2)
