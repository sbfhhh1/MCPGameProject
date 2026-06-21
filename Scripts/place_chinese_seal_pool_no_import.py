# -*- coding: utf-8 -*-
import json
import unreal

MAP_PATH = "/Game/TransformationVFX/SM2SM/SM2SM"
OUT = r"C:/UE_Project/MCPGameProject/Scripts/_chinese_seal_pool_setup.json"
LABEL = "Chinese_Seal_Pool_Animator"
WATER_LOCATION = unreal.Vector(350.0, 0.0, 60.0)


def log(msg):
    unreal.log("[ChineseSealPoolNoImport] " + msg)


def destroy_existing():
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if actor.get_actor_label() == LABEL:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass


def main():
    loaded = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    log("load_map({}) -> {}".format(MAP_PATH, loaded))

    actor_class = unreal.load_class(None, "/Script/MCPGameProject.ChineseSealPoolAnimator")
    if not actor_class:
        raise RuntimeError("AChineseSealPoolAnimator class is not loaded.")

    destroy_existing()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        WATER_LOCATION,
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(LABEL)
    actor.tags = [unreal.Name("WaterPool"), unreal.Name("ChineseSealPool")]

    actor.set_editor_property("Rows", 4)
    actor.set_editor_property("Columns", 4)
    actor.set_editor_property("RowSpacing", 70.0)
    actor.set_editor_property("ColumnSpacing", 70.0)
    actor.set_editor_property("SealScale", 0.75)
    actor.set_editor_property("HeightAboveWater", 3.0)
    actor.set_editor_property("AnimationAmplitude", 4.5)
    actor.set_editor_property("AnimationSpeed", 0.32)
    actor.set_editor_property("AnimationFrequency", 1.0)
    actor.set_editor_property("Irregularity", 0.68)
    actor.set_editor_property("NoiseScale", 0.55)
    actor.set_editor_property("RandomSeed", 1937)
    actor.set_editor_property("bEnableAnimation", True)
    actor.set_editor_property("bAnimateInEditor", True)

    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    result = {
        "actor_label": actor.get_actor_label(),
        "actor_name": actor.get_name(),
        "class": actor.get_class().get_name(),
        "location": [WATER_LOCATION.x, WATER_LOCATION.y, WATER_LOCATION.z],
        "rows": 4,
        "columns": 4,
        "source": "SourceArt/ChineseSeals/chinese_seals_meshes.sealmesh",
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    log("setup complete: " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"error": str(exc), "traceback": tb}, fh, ensure_ascii=False, indent=2)
        unreal.log_error("[ChineseSealPoolNoImport] " + tb)
        raise
