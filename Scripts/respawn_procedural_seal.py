# -*- coding: utf-8 -*-
"""销毁并重新生成 Chinese_Seal_Pool_Animator（程序网格路径），
使新编译的法线/坐标转换逻辑生效。全新实例触发 OnConstruction
重新解析 .sealmesh 并用新代码构建截面数据。忠实复制原有参数。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_respawn_procedural_seal.json"
LABEL = "Chinese_Seal_Pool_Animator"

COPY_PROPS = [
    "OverrideMaterial",
    "Rows", "Columns", "RowSpacing", "ColumnSpacing", "SealScale",
    "SealHeightToSectionRatio", "HeightAboveWater",
    "DefaultSealColor", "DefaultSealMetallic", "DefaultSealRoughness", "DefaultSealSpecular",
    "bEnableAnimation", "bAnimateInEditor", "AnimationAmplitude", "AnimationSpeed",
    "AnimationFrequency", "Irregularity", "NoiseScale", "RandomSeed",
]


def main():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old = None
    for cand in actor_subsystem.get_all_level_actors():
        if cand.get_class().get_name() == "ChineseSealPoolAnimator":
            old = cand
            break
    if not old:
        raise RuntimeError("ChineseSealPoolAnimator actor not found in level")

    location = old.get_actor_location()
    rotation = old.get_actor_rotation()
    tags = list(old.tags)

    saved = {}
    for prop in COPY_PROPS:
        try:
            saved[prop] = old.get_editor_property(prop)
        except Exception as exc:
            saved[prop] = None
            unreal.log_warning("[respawn] cannot read %s: %s" % (prop, exc))

    actor_class = old.get_class()
    unreal.EditorLevelLibrary.destroy_actor(old)

    new = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)
    new.set_actor_label(LABEL)
    if tags:
        new.tags = tags

    new.set_editor_property("SealMeshes", [])  # 保持空 -> 走程序网格路径
    for prop, value in saved.items():
        if value is None:
            continue
        try:
            new.set_editor_property(prop, value)
        except Exception as exc:
            unreal.log_warning("[respawn] cannot set %s: %s" % (prop, exc))

    new.rerun_construction_scripts()

    proc_count = len(new.get_components_by_class(unreal.ProceduralMeshComponent))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    try:
        unreal.EditorLevelLibrary.save_current_level()
    except Exception as exc:
        unreal.log_warning("[respawn] save_current_level failed: " + str(exc))

    result = {
        "label": new.get_actor_label(),
        "class": actor_class.get_name(),
        "procedural_components": proc_count,
        "copied_props": list(saved.keys()),
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    unreal.log("[respawn] " + json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
