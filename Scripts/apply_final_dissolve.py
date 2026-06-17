import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
MI_NAMES = ["MI_Burst_Jade_YF", "MI_Burst_Jade_TYS", "MI_Burst_Jade_YZL"]

for name in MI_NAMES:
    mi = unreal.load_asset(f"{DIR}/{name}")
    if not mi:
        continue
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Tile", 0.08)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Contrast", 2.0)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Edge", 0.1)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Amount", 1.0)
    mel.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    unreal.log(f"[JadeFinal] {name}: Tile=0.08 Contrast=2.0 Edge=0.1 Dissolve=1.0")

# 恢复编辑器可见性（probe 之前隐藏了 B/C），运行时由 C++ 管理
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
a = next((x for x in actors if x.get_actor_label() == "BP_Burst_SM_Test"), None)
if a:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_name().replace(" ", "").replace("_", "")
        if "StaticMeshA" in n:
            c.set_visibility(True)
        elif "StaticMeshB" in n or "StaticMeshC" in n:
            c.set_visibility(False)

unreal.log("[JadeFinal] DONE")
