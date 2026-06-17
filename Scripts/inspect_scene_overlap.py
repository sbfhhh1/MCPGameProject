import unreal

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

def comp_info(c):
    loc = c.get_world_location()
    mat = c.get_material(0)
    return (f"vis={c.is_visible()} hiddenGame={c.is_visibility_based_anim_tick_option if False else ''} "
            f"loc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) "
            f"mesh={c.get_editor_property('static_mesh').get_name() if c.get_editor_property('static_mesh') else None} "
            f"mat0={mat.get_name() if mat else None}")

burst = next((a for a in actors if a.get_actor_label() == "BP_Burst_SM_Test"), None)
if burst:
    unreal.log("[Scene] === BP_Burst_SM_Test components ===")
    for c in burst.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_name().replace(" ", "").replace("_", "")
        if any(e in n for e in ["StaticMeshA", "StaticMeshB", "StaticMeshC"]):
            unreal.log(f"[Scene] {c.get_name()}: {comp_info(c)}")

for label in ["YF", "TYS", "YZL"]:
    src = next((a for a in actors if a.get_actor_label() == label), None)
    if src:
        comps = src.get_components_by_class(unreal.StaticMeshComponent)
        c = comps[0] if comps else None
        loc = src.get_actor_location()
        info = comp_info(c) if c else "no mesh comp"
        unreal.log(f"[Scene] SRC {label}: actorHiddenGame={src.is_hidden_ed()} actorLoc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) {info}")
    else:
        unreal.log(f"[Scene] SRC {label}: NOT FOUND")

unreal.log("[Scene] DONE")
