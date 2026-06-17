import unreal
import json

with open("C:/UE_Project/MCPGameProject/Saved/mid_test.json", "r") as f:
    val = json.load(f)["dissolve"]

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
a = next(x for x in actors if x.get_actor_label() == "BP_Burst_SM_Test")
compA = None
for c in a.get_components_by_class(unreal.StaticMeshComponent):
    n = c.get_name().replace(" ", "").replace("_", "")
    if "StaticMeshA" in n:
        compA = c
    elif "StaticMeshB" in n or "StaticMeshC" in n:
        c.set_visibility(False)
compA.set_visibility(True)

mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YF")
# 和 C++ PIE 完全相同：component 创建动态材质实例，再动态设 Dissolve
mid = compA.create_dynamic_material_instance(0, mi)
mid.set_scalar_parameter_value("Dissolve Amount", val)
unreal.log(f"[MIDTest] applied MID Dissolve={val} on StaticMeshA")
