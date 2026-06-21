# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_set_chinese_seal_defaults.json"
LABEL = "Chinese_Seal_Pool_Animator"
LOCATION = unreal.Vector(350.0, 0.0, 60.0)
SEAL_MATERIAL = "/Game/TransformationVFX/SM2SM/ChineseSeals/M_ChineseSeal_DefaultWhite.M_ChineseSeal_DefaultWhite"


DEFAULTS = {
    "Rows": 16,
    "Columns": 8,
    "RowSpacing": 25.0,
    "ColumnSpacing": 25.0,
    "SealScale": 0.32,
    "SealHeightToSectionRatio": 2.0,
    "HeightAboveWater": 3.0,
    "DefaultSealColor": unreal.LinearColor(1.0, 1.0, 1.0, 1.0),
    "DefaultSealMetallic": 0.0,
    "DefaultSealRoughness": 0.5,
    "DefaultSealSpecular": 0.5,
    "bUseImportedStaticMeshes": True,
}


def main():
    result = {"destroyed": 0, "defaults": {}}
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actor_subsystem.get_all_level_actors():
        if actor.get_actor_label() == LABEL:
            actor_subsystem.destroy_actor(actor)
            result["destroyed"] += 1

    actor_class = unreal.load_class(None, "/Script/MCPGameProject.ChineseSealPoolAnimator")
    if not actor_class:
        raise RuntimeError("ChineseSealPoolAnimator class is not loaded")

    actor = actor_subsystem.spawn_actor_from_class(actor_class, LOCATION, unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(LABEL)
    actor.tags = [unreal.Name("WaterPool"), unreal.Name("ChineseSealPool")]

    seal_material = unreal.load_asset(SEAL_MATERIAL)
    actor.set_editor_property("OverrideMaterial", seal_material)
    result["override_material"] = SEAL_MATERIAL if seal_material else None


    for key, value in DEFAULTS.items():
        actor.set_editor_property(key, value)
        if isinstance(value, unreal.LinearColor):
            result["defaults"][key] = [value.r, value.g, value.b, value.a]
        else:
            result["defaults"][key] = value

    # Rebuild by moving a no-op construction-affecting property path: respawn already used C++ defaults,
    # and the properties above are persisted for future construction/load.
    result["actor"] = actor.get_actor_label()
    result["location"] = [LOCATION.x, LOCATION.y, LOCATION.z]
    result["save_current_level"] = bool(unreal.EditorLevelLibrary.save_current_level())
    result["save_dirty_packages"] = bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[SetChineseSealDefaults] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
