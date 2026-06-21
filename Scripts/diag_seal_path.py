# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_diag_seal_path.json"
LABEL = "Chinese_Seal_Pool_Animator"


def main():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = None
    for cand in actor_subsystem.get_all_level_actors():
        if cand.get_actor_label() == LABEL:
            actor = cand
            break
    if not actor:
        raise RuntimeError("Actor not found: " + LABEL)

    seal_meshes = actor.get_editor_property("SealMeshes")
    result = {
        "actor": actor.get_actor_label(),
        "actor_location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "seal_meshes_count": len(seal_meshes) if seal_meshes else 0,
        "seal_meshes": [m.get_path_name() if m else None for m in (seal_meshes or [])],
        "static_components": 0,
        "procedural_components": 0,
        "component_classes": {},
        "sample_bounds": None,
    }

    comps = actor.get_components_by_class(unreal.MeshComponent)
    for c in comps:
        cls = c.get_class().get_name()
        result["component_classes"][cls] = result["component_classes"].get(cls, 0) + 1
        if "Procedural" in cls:
            result["procedural_components"] += 1
        elif "StaticMesh" in cls:
            result["static_components"] += 1

    # sample first component bounds + scale
    if comps:
        c0 = comps[0]
        try:
            origin, ext = c0.get_local_bounds()
            result["sample_bounds"] = {
                "name": c0.get_name(),
                "rel_scale": [c0.get_relative_scale3d().x, c0.get_relative_scale3d().y, c0.get_relative_scale3d().z],
            }
        except Exception as exc:
            result["sample_bounds"] = {"error": str(exc)}

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[diag_seal_path] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
