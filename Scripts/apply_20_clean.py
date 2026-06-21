# -*- coding: utf-8 -*-
"""在 SM2SM 关卡用现有20个隶书资产配置pool显示20种。不导入FBX。结果写UE日志。"""
import unreal, json

ASSET_DIR = "/Game/TransformationVFX/SM2SM/ChineseSeals"
TOKENS = ["Shui", "Guang", "Ying", "Feng", "Yun", "Shi", "Huo", "Shan", "Hai", "Lin",
          "Lei", "Dian", "Yu", "Xue", "Yue", "Ri", "Xing", "Tian", "Di", "Chuan"]

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

meshes = []
for t in TOKENS:
    m = unreal.EditorAssetLibrary.load_asset("%s/SM_Seal_%s.SM_Seal_%s" % (ASSET_DIR, t, t))
    if m:
        meshes.append(m)

pool = None
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break

if not pool or len(meshes) != 20:
    unreal.log("[apply20] ABORT pool=%s meshes=%d" % (bool(pool), len(meshes)))
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
    new.set_editor_property("SealMeshes", meshes)
    new.set_editor_property("bEnableAnimation", True)
    new.set_editor_property("bAnimateInEditor", True)

    comps = new.get_components_by_class(unreal.StaticMeshComponent)
    for i, c in enumerate(comps):
        c.set_static_mesh(meshes[i % len(meshes)])

    kinds = set()
    for c in comps:
        m = c.get_editor_property("static_mesh")
        if m:
            kinds.add(m.get_name())

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    saved = False
    try:
        saved = bool(unreal.EditorLevelLibrary.save_current_level())
    except Exception as e:
        saved = "ERR"

    unreal.log("[apply20] RESULT static_comp=%d distinct_kinds=%d seal_meshes=%d saved=%s" %
               (len(comps), len(kinds), len(new.get_editor_property("SealMeshes")), saved))
