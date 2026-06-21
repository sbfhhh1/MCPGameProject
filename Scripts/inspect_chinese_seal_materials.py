# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_inspect_chinese_seal_materials.json"
LABEL = "Chinese_Seal_Pool_Animator"


def path_of(obj):
    return obj.get_path_name() if obj else None


def main():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    result = {"actor": None, "override_material": None, "components": []}

    actor = None
    for candidate in actor_subsystem.get_all_level_actors():
        if candidate.get_actor_label() == LABEL:
            actor = candidate
            break

    if not actor:
        raise RuntimeError("Actor not found: " + LABEL)

    result["actor"] = actor.get_actor_label()
    result["override_material"] = path_of(actor.get_editor_property("OverrideMaterial"))

    components = actor.get_components_by_class(unreal.MeshComponent)
    for component in components[:8]:
        result["components"].append(
            {
                "name": component.get_name(),
                "material_0": path_of(component.get_material(0)),
            }
        )

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[InspectChineseSealMaterials] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
