import unreal
import json
import os

# 策略：基于 M_YZL_ProceduralJade_SSS 创建一个带溶解逻辑的新材质
# 1. 复制 M_YZL_ProceduralJade_SSS 为 M_YZL_JadeDissolve
# 2. 修改 Blend Mode 为 Translucent
# 3. 添加溶解参数和节点逻辑
# 4. 创建材质实例 MI_YZL_JadeDissolve

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
source_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
dest_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"

# 检查目标是否已存在
existing = unreal.load_asset(dest_path)
if existing:
    r = {"status": "exists", "path": dest_path}
else:
    # 复制材质资产
    source_asset = unreal.load_asset(source_path)
    if source_asset:
        # 使用duplicate_asset
        new_mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source_asset)
        if new_mat:
            r = {"status": "created", "path": new_mat.get_path_name(), "class": new_mat.get_class().get_name()}
        else:
            r = {"status": "duplicate_failed"}
    else:
        r = {"status": "source_not_found"}

with open(os.path.join(os.environ["USERPROFILE"], "ue5_create_result.json"), "w") as f:
    json.dump(r, f, indent=2)
