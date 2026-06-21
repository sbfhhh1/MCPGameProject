# -*- coding: utf-8 -*-
import unreal, json
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = sub.get_all_level_actors()
pool = None
for a in acts:
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break
r = {"total_actors": len(acts), "has_pool": bool(pool)}
if pool:
    sm = pool.get_components_by_class(unreal.StaticMeshComponent)
    pm = pool.get_components_by_class(unreal.ProceduralMeshComponent)
    kinds = set()
    for c in sm:
        m = c.get_editor_property("static_mesh")
        if m:
            kinds.add(m.get_name())
    sims = pool.get_editor_property("SealMeshes")
    r["pool_static_comp"] = len(sm)
    r["pool_proc_comp"] = len(pm)
    r["pool_distinct_kinds"] = len(kinds)
    r["pool_seal_meshes_prop"] = len(sims) if sims else 0
with open(r"C:/UE_Project/MCPGameProject/Scripts/_pool_now.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(r))
unreal.log("[check_pool_now] " + json.dumps(r))
