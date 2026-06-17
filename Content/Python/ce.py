import unreal, json, os
r = {"mp": [x for x in dir(unreal.MaterialProperty) if not x.startswith('_') and x[0].isupper()]}
with open(os.path.join(os.environ["USERPROFILE"], "e.json"), "w") as f:
    json.dump(r, f)
