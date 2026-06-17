import unreal, json, os

r = {}

# Step 1: 创建材质实例
mi_path = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve"
if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
    unreal.EditorAssetLibrary.delete_asset(mi_path)
    r["deleted"] = True

try:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = asset_tools.create_asset("MI_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", unreal.MaterialInstanceConstant, None)
    r["mi"] = mi.get_path_name() if mi else "None"
except Exception as e:
    r["create_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "r1.json"), "w") as f:
    json.dump(r, f, indent=2)
