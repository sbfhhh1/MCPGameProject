# -*- coding: utf-8 -*-
"""load SM2SM + 设 pool 初始值 + 保存，一气呵成。"""
import unreal, json
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/TransformationVFX/SM2SM/SM2SM")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pool = None
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break
if not pool:
    unreal.log("[load_set] NO_POOL actors=%d" % len(sub.get_all_level_actors()))
else:
    pool.set_editor_property("Rows", 8)
    pool.set_editor_property("Columns", 9)
    pool.set_editor_property("RowSpacing", 25.0)
    pool.set_editor_property("ColumnSpacing", 25.0)
    pool.set_editor_property("SealScale", 0.32)
    pool.set_editor_property("SealHeightToSectionRatio", 2.0)
    pool.set_editor_property("HeightAboveWater", 3.0)
    pool.set_actor_location(unreal.Vector(450.0, 0.0, 162.5), False, False)
    pool.set_actor_rotation(unreal.Rotator(0.0, 90.0, 90.0), False)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    try:
        unreal.EditorLevelLibrary.save_current_level()
    except Exception:
        pass
    unreal.log("[load_set] DONE Rows=%d Cols=%d proc=%d" % (
        pool.get_editor_property("Rows"), pool.get_editor_property("Columns"),
        len(pool.get_components_by_class(unreal.ProceduralMeshComponent))))
