# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_restore_burst_sm_test_instance.json"
LABEL = "BP_Burst_SM_Test"


def main():
    result = {"found": False, "actions": []}
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    actor = next((a for a in actors if a.get_actor_label() == LABEL), None)
    if not actor:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        unreal.log_warning("[RestoreBurstSMTest] BP_Burst_SM_Test not found")
        return

    result["found"] = True
    actor.set_actor_location(unreal.Vector(250.0, 0.0, 170.0), False, False)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    actor.set_actor_scale3d(unreal.Vector(200.0, 200.0, 200.0))
    result["actions"].append("reset actor transform")

    for comp in actor.get_components_by_class(unreal.ActorComponent):
        name = comp.get_name()
        cls = comp.get_class().get_name()

        if isinstance(comp, unreal.StaticMeshComponent):
            normalized = name.replace(" ", "").lower()
            if "staticmesha" in normalized:
                comp.set_visibility(True, True)
                comp.set_hidden_in_game(False, True)
                result["actions"].append("show Static Mesh A")
            elif "staticmeshb" in normalized or "staticmeshc" in normalized:
                comp.set_visibility(False, True)
                comp.set_hidden_in_game(True, True)
                result["actions"].append("hide " + name)

        if "NiagaraComponent" in cls:
            try:
                comp.deactivate_immediate()
            except Exception:
                try:
                    comp.deactivate()
                except Exception:
                    pass
            try:
                comp.set_visibility(False, True)
                comp.set_hidden_in_game(True, True)
            except Exception:
                pass
            result["actions"].append("stop and hide Niagara")

        if "WidgetComponent" in cls:
            try:
                comp.set_visibility(False, True)
                comp.set_hidden_in_game(True, True)
            except Exception:
                pass
            result["actions"].append("hide widget")

    try:
        unreal.EditorLevelLibrary.save_current_level()
        result["saved_level"] = True
    except Exception as exc:
        result["saved_level"] = False
        result["save_error"] = str(exc)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[RestoreBurstSMTest] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
