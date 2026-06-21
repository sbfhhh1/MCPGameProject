# -*- coding: utf-8 -*-
"""respawn pool 为程序网格模式：读新.sealmesh(20字隶书)，20印章，呼吸动画。结果写UE日志。"""
import unreal, json

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pool = None
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break

if not pool:
    unreal.log("[respawn_proc] ABORT no pool")
else:
    loc = pool.get_actor_location()
    rot = pool.get_actor_rotation()
    tags = list(pool.tags)
    cls = pool.get_class()
    sub.destroy_actor(pool)

    new = sub.spawn_actor_from_class(cls, loc, rot)
    new.set_actor_label("Chinese_Seal_Pool_Animator")
    if tags:
        new.tags = tags
    # 程序网格路径
    new.set_editor_property("bUseImportedStaticMeshes", False)
    new.set_editor_property("SealMeshes", [])
    # 20 印章 5x4
    new.set_editor_property("Rows", 5)
    new.set_editor_property("Columns", 4)
    new.set_editor_property("RowSpacing", 70.0)
    new.set_editor_property("ColumnSpacing", 70.0)
    # 呼吸动画
    new.set_editor_property("bEnableAnimation", True)
    new.set_editor_property("bAnimateInEditor", True)

    # 触发重建（set 属性后让 OnConstruction 重跑，走程序网格读新.sealmesh）
    rebuilt = "none"
    try:
        new.rerun_construction_scripts()
        rebuilt = "rerun"
    except Exception:
        new.set_actor_location(loc + unreal.Vector(0, 0, 0.1), False, False)
        new.set_actor_location(loc, False, False)
        rebuilt = "nudge"

    sm = len(new.get_components_by_class(unreal.StaticMeshComponent))
    pm = len(new.get_components_by_class(unreal.ProceduralMeshComponent))

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    saved = False
    try:
        saved = bool(unreal.EditorLevelLibrary.save_current_level())
    except Exception:
        saved = "ERR"

    unreal.log("[respawn_proc] " + json.dumps({
        "static_comp": sm, "proc_comp": pm, "rebuilt": rebuilt, "saved": saved,
        "use_imported": new.get_editor_property("bUseImportedStaticMeshes"),
    }, default=str))
