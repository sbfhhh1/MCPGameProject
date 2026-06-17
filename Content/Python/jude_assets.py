import unreal, json, os

r = {}

# 搜索BurstJade目录下所有材质实例
asset_reg = unreal.EditorAssetLibrary
# 列出jude目录下的资产
assets = unreal.EditorAssetLibrary.list_assets("/Game/TransformationVFX/SM2SM/jude", recursive=True, include_folder=False)
r["assets"] = [str(a) for a in assets]

with open(os.path.join(os.environ["USERPROFILE"], "jude_assets.json"), "w") as f:
    json.dump(r, f, indent=2)
