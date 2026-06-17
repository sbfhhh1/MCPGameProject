import unreal
import json

mel = unreal.MaterialEditingLibrary
DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"

with open("C:/UE_Project/MCPGameProject/Saved/yf_full_params.json", "r") as f:
    p = json.load(f)

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

mi = unreal.load_asset(f"{DIR}/MI_Burst_Jade_YF")
mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Tile", p["tile"])
mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Contrast", p["contrast"])
mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Edge", p["edge"])
mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Amount", p["dissolve"])
mel.update_material_instance(mi)
unreal.log(f"[YFFull] tile={p['tile']} contrast={p['contrast']} edge={p['edge']} dissolve={p['dissolve']}")
