# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_burst_test_instance_inspect.json"
LABEL = "BP_Burst_SM_Test"


def v3(v):
    return [float(v.x), float(v.y), float(v.z)]


def main():
    result = {"found": False}
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.get_actor_label() != LABEL:
            continue
        result["found"] = True
        result["name"] = actor.get_name()
        result["class"] = actor.get_class().get_name()
        result["location"] = v3(actor.get_actor_location())
        result["rotation"] = [
            float(actor.get_actor_rotation().pitch),
            float(actor.get_actor_rotation().yaw),
            float(actor.get_actor_rotation().roll),
        ]
        result["scale"] = v3(actor.get_actor_scale3d())
        comps = []
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            item = {
                "name": comp.get_name(),
                "class": comp.get_class().get_name(),
            }
            if isinstance(comp, unreal.StaticMeshComponent):
                mesh = comp.get_editor_property("static_mesh")
                item["mesh"] = mesh.get_path_name() if mesh else None
                mats = []
                for idx in range(comp.get_num_materials()):
                    mat = comp.get_material(idx)
                    mats.append(mat.get_path_name() if mat else None)
                item["materials"] = mats
                item["visible"] = comp.is_visible()
                item["relative_location"] = v3(comp.get_editor_property("relative_location"))
                item["relative_scale"] = v3(comp.get_editor_property("relative_scale3d"))
            if "Switcher" in item["class"]:
                for prop in [
                    "StateFadeMaterials",
                    "StateDissolveMaterials",
                    "SourceHideDelay",
                    "SourceFadeOutDuration",
                    "ModelSwitchDuration",
                    "bEnableKeyboardInput",
                ]:
                    try:
                        val = comp.get_editor_property(prop)
                        if isinstance(val, list):
                            item[prop] = [x.get_path_name() if x else None for x in val]
                        else:
                            item[prop] = str(val)
                    except Exception:
                        pass
            comps.append(item)
        result["components"] = comps
        break

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[InspectBurstTest] " + json.dumps(result, ensure_ascii=False))


main()
