"""恢复脚本：把所有以 M_YZL_ProceduralJade_SSS 为父的玉石材质实例重新挂回父材质。

背景：之前 create 脚本用 delete_asset 删除并重建父材质，导致这些实例在内存中失去父级
（显示默认棋盘格）。本脚本重新设置父级即可恢复，并把语义已随“UV 不规则点状沁色”改变的
两个参数（Scale=UV 平铺数、Contrast=斑点边缘锐度）设为合理 UV 值。
"""
import unreal

MATERIAL_PATH = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"

# 所有以该程序化玉石材质为父的 SSS 材质实例。
SSS_INSTANCES = [
    "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_YF_SSS",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_TYS_SSS",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_YZL_SSS",
]

# UV 空间下的沁色参数（语义已变）：Scale=平铺次数(越大越密)，Contrast=边缘锐度(0..1)。
UV_STAIN_SCALE = 6.0
UV_STAIN_CONTRAST = 0.4

mel = unreal.MaterialEditingLibrary
material = unreal.load_asset(MATERIAL_PATH)
if material is None:
    raise RuntimeError(f"找不到父材质 {MATERIAL_PATH}，请先成功运行 create_yzl_procedural_jade_sss.py")

fixed = 0
for path in SSS_INSTANCES:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log_warning(f"[ReparentJade] 跳过不存在的实例：{path}")
        continue
    instance = unreal.load_asset(path)
    mel.set_material_instance_parent(instance, material)
    mel.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Scale", UV_STAIN_SCALE)
    mel.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Contrast", UV_STAIN_CONTRAST)
    mel.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    fixed += 1
    unreal.log(f"[ReparentJade] 已重挂父级并设 UV 沁色参数：{path}")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log(f"[ReparentJade] 完成，共修复 {fixed} 个材质实例")
