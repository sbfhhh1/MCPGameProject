import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
MI_NAMES = ["MI_Burst_Jade_YF", "MI_Burst_Jade_TYS", "MI_Burst_Jade_YZL"]

# 更明显的溶解：更软的边缘(低 Contrast) + 更大的噪波块(更小 Tile)
for name in MI_NAMES:
    mi = unreal.load_asset(f"{DIR}/{name}")
    if not mi:
        continue
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Contrast", 2.0)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Tile", 0.02)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Edge", 0.35)
    mel.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    unreal.log(f"[JadeTune] {name}: Contrast=2.0 Tile=0.02 Edge=0.35")

unreal.log("[JadeTune] DONE")
