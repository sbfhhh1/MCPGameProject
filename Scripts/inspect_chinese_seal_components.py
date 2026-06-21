# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_inspect_chinese_seal_components.json"
LABEL = "Chinese_Seal_Pool_Animator"


def obj_path(obj):
    return obj.get_path_name() if obj else None


def main():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = None
    for candidate in actor_subsystem.get_all_level_actors():
        if candidate.get_actor_label() == LABEL:
            actor = candidate
            break
    if not actor:
        raise RuntimeError("Actor not found")

    result = {
        "actor": actor.get_actor_label(),
        "bUseImportedStaticMeshes": bool(actor.get_editor_property("bUseImportedStaticMeshes")),
        "components": [],
    }

    for component in actor.get_components_by_class(unreal.MeshComponent)[:12]:
        item = {
            "name": component.get_name(),
            "class": component.get_class().get_name(),
            "material_0": obj_path(component.get_material(0)),
        }
        if isinstance(component, unreal.StaticMeshComponent):
            item["static_mesh"] = obj_path(component.get_editor_property("static_mesh"))
        result["components"].append(item)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[InspectChineseSealComponents] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
