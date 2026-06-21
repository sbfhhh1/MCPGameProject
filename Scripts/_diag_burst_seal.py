"""只读诊断：dump BP_Burst_SM_Test 的网格材质、状态切换器材质数组、玉石实例父级，
以及印章 Animator 的材质设置。不修改任何资产，无崩溃风险。结果写入 _diag_burst_seal.json。"""
import unreal
import json


def path_of(obj):
    return obj.get_path_name() if obj else None


def array_paths(value):
    try:
        return [path_of(x) for x in value]
    except TypeError:
        return path_of(value)


out = {"burst_actor": {}, "switcher": {}, "instance_parents": {}, "seal": {}}

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = actor_sub.get_all_level_actors()

# ---- BP_Burst_SM_Test 关卡实例 ----
burst = next((a for a in all_actors if a.get_actor_label() == "BP_Burst_SM_Test"), None)
if burst:
    for comp in burst.get_components_by_class(unreal.StaticMeshComponent):
        mats = []
        for i in range(max(comp.get_num_materials(), 1)):
            m = comp.get_material(i)
            mats.append(path_of(m))
        sm = comp.get_editor_property("static_mesh")
        out["burst_actor"][comp.get_name()] = {"materials": mats, "static_mesh": path_of(sm)}

    switcher = burst.get_component_by_class(unreal.BurstMeshStateSwitcherComponent)
    if switcher:
        for prop in ["StateFadeMaterials", "StateDissolveMaterials", "StateParticleMaterials",
                     "MorphParticleSystem", "ParticleMaterial", "ParticleSystem"]:
            try:
                out["switcher"][prop] = array_paths(switcher.get_editor_property(prop))
            except Exception as exc:
                out["switcher"][prop] = f"ERR {exc}"
    else:
        out["switcher"] = "BurstMeshStateSwitcherComponent NOT FOUND on actor"
else:
    out["burst_actor"] = "actor BP_Burst_SM_Test NOT FOUND"

# ---- BurstJade 文件夹里所有材质实例的父级 ----
for asset_path in unreal.EditorAssetLibrary.list_assets(
        "/Game/TransformationVFX/SM2SM/jude/BurstJade", recursive=False, include_folder=False):
    clean = asset_path.split(".")[0]
    obj = unreal.load_asset(clean)
    if isinstance(obj, unreal.MaterialInstanceConstant):
        out["instance_parents"][clean] = path_of(obj.get_editor_property("parent"))

# ---- 印章 Animator ----
seal = next((a for a in all_actors
             if "SealPool" in a.get_class().get_name() or "Seal_Pool" in a.get_actor_label()), None)
if seal:
    out["seal"]["class"] = seal.get_class().get_name()
    out["seal"]["label"] = seal.get_actor_label()
    for prop in ["DefaultSealColor", "DefaultSealMetallic", "DefaultSealRoughness", "OverrideMaterial"]:
        try:
            v = seal.get_editor_property(prop)
            out["seal"][prop] = path_of(v) if isinstance(v, unreal.Object) else str(v)
        except Exception as exc:
            out["seal"][prop] = f"ERR {exc}"
    comp_mats = {}
    for comp in seal.get_components_by_class(unreal.MeshComponent):
        mats = [path_of(comp.get_material(i)) for i in range(max(comp.get_num_materials(), 1))]
        comp_mats[comp.get_name() + " (" + comp.get_class().get_name() + ")"] = mats
    out["seal"]["mesh_materials"] = comp_mats
else:
    out["seal"] = "seal actor NOT FOUND"

with open("C:/UE_Project/MCPGameProject/Scripts/_diag_burst_seal.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(out, ensure_ascii=False, indent=2))
unreal.log("[Diag] wrote _diag_burst_seal.json")
