# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_set_burst_initial_material.json"
LABEL = "BP_Burst_SM_Test"
INITIAL_MATERIAL = "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YF_Jade_TYS_SSS"


def main():
    result = {
        "actor_found": False,
        "material": INITIAL_MATERIAL,
        "actions": [],
    }
    mat = unreal.EditorAssetLibrary.load_asset(INITIAL_MATERIAL)
    if not mat:
        raise RuntimeError("Material not found: " + INITIAL_MATERIAL)

    actor = next(
        (a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == LABEL),
        None,
    )
    if not actor:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        unreal.log_warning("[SetBurstInitialMaterial] Actor not found: " + LABEL)
        return

    result["actor_found"] = True

    for comp in actor.get_components_by_class(unreal.ActorComponent):
        name = comp.get_name()
        cls = comp.get_class().get_name()
        normalized = name.replace(" ", "").lower()

        if isinstance(comp, unreal.StaticMeshComponent):
            if "staticmesha" in normalized:
                comp.set_material(0, mat)
                comp.set_visibility(True, True)
                comp.set_hidden_in_game(False, True)
                result["actions"].append("set Static Mesh A material and show it")
            elif "staticmeshb" in normalized or "staticmeshc" in normalized:
                comp.set_visibility(False, True)
                comp.set_hidden_in_game(True, True)
                result["actions"].append("hide " + name)

        if "BurstMeshStateSwitcherComponent" in cls:
            try:
                current = list(comp.get_editor_property("StateFadeMaterials"))
            except Exception:
                current = []
            while len(current) < 3:
                current.append(None)
            current[0] = mat
            comp.set_editor_property("StateFadeMaterials", current)
            result["actions"].append("set StateFadeMaterials[0] for runtime initial load")

        if "NiagaraComponent" in cls:
            try:
                comp.deactivate_immediate()
            except Exception:
                try:
                    comp.deactivate()
                except Exception:
                    pass
            comp.set_visibility(False, True)
            comp.set_hidden_in_game(True, True)
            result["actions"].append("stop and hide Niagara")

    result["save_current_level"] = bool(unreal.EditorLevelLibrary.save_current_level())
    result["save_dirty_packages"] = bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[SetBurstInitialMaterial] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
