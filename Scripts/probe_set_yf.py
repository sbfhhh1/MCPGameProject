import unreal

# 读取一个 sidecar 值文件决定 Dissolve（规避无法传参）
try:
    with open("C:/UE_Project/MCPGameProject/Saved/yf_probe_value.txt", "r") as f:
        value = float(f.read().strip())
except Exception:
    value = 1.0

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
a = next(x for x in actors if x.get_actor_label() == "BP_Burst_SM_Test")
comps = {}
for c in a.get_components_by_class(unreal.StaticMeshComponent):
    n = c.get_name().replace(" ", "").replace("_", "")
    for e in ["StaticMeshA", "StaticMeshB", "StaticMeshC"]:
        if e in n:
            comps[e] = c
comps["StaticMeshB"].set_visibility(False)
comps["StaticMeshC"].set_visibility(False)
comps["StaticMeshA"].set_visibility(True)

mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YF")
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Dissolve Amount", value)
unreal.MaterialEditingLibrary.update_material_instance(mi)
unreal.log(f"[YFProbe] set YF Dissolve Amount={value}, only StaticMeshA visible")
