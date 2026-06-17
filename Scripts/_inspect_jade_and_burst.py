import unreal

LOG = "[INSPECT_JB]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))

ar = unreal.AssetRegistryHelpers.get_asset_registry()

# 1. 扫描 jade 相关目录
for folder in ["/Game/TransformationVFX/SM2SM", "/Game/TransformationVFX/SM2SM/jude"]:
    try:
        assets = unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False)
        log("FOLDER {} -> {} assets".format(folder, len(assets)))
        for a in assets:
            data = ar.get_asset_by_object_path(a)
            cls = str(data.asset_class_path.asset_name) if data else "?"
            log("  ASSET {} [{}]".format(a, cls))
    except Exception as e:
        log("folder {} error: {}".format(folder, e))

# 2. 找所有 StaticMesh 资产里名字含 jade/yzl/jude 的
log("--- search jade meshes ---")
try:
    all_assets = unreal.EditorAssetLibrary.list_assets("/Game/TransformationVFX", recursive=True, include_folder=False)
    for a in all_assets:
        low = a.lower()
        if any(k in low for k in ["jade","jude","yzl"]):
            data = ar.get_asset_by_object_path(a)
            cls = str(data.asset_class_path.asset_name) if data else "?"
            log("  JADE {} [{}]".format(a, cls))
except Exception as e:
    log("search error: {}".format(e))

# 3. 找 BP_Burst_SM 相关蓝图
log("--- search BP_Burst ---")
try:
    bps = unreal.EditorAssetLibrary.list_assets("/Game/TransformationVFX/BP", recursive=True, include_folder=False)
    for a in bps:
        log("  BP {}".format(a))
except Exception as e:
    log("bp search error: {}".format(e))

# 4. 找 SM2SM 关卡
log("--- search levels (Worlds) ---")
try:
    all_g = unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
    for a in all_g:
        data = ar.get_asset_by_object_path(a)
        if data and str(data.asset_class_path.asset_name) == "World":
            log("  LEVEL {}".format(a))
except Exception as e:
    log("level search error: {}".format(e))

log("DONE")
