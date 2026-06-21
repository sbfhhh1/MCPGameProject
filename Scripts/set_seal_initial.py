# -*- coding: utf-8 -*-
"""只设 pool 的初始值（截图 Layout + Transform），别的不动。结果写UE日志。"""
import unreal, json

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pool = None
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break

if not pool:
    unreal.log("[set_initial] ABORT no pool")
else:
    pool.set_editor_property("Rows", 8)
    pool.set_editor_property("Columns", 9)
    pool.set_editor_property("RowSpacing", 25.0)
    pool.set_editor_property("ColumnSpacing", 25.0)
    pool.set_editor_property("SealScale", 0.32)
    pool.set_editor_property("SealHeightToSectionRatio", 2.0)
    pool.set_editor_property("HeightAboveWater", 3.0)
    pool.set_actor_location(unreal.Vector(450.0, 0.0, 162.5), False, False)
    pool.set_actor_rotation(unreal.Rotator(0.0, 90.0, 90.0), False)  # Roll90 Pitch0 Yaw90

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    saved = False
    try:
        saved = bool(unreal.EditorLevelLibrary.save_current_level())
    except Exception:
        saved = "ERR"
    loc = pool.get_actor_location()
    rot = pool.get_actor_rotation()
    unreal.log("[set_initial] " + json.dumps({
        "Rows": pool.get_editor_property("Rows"),
        "Columns": pool.get_editor_property("Columns"),
        "loc": [loc.x, loc.y, loc.z],
        "rot": [rot.roll, rot.pitch, rot.yaw],
        "saved": saved,
    }, default=str))
