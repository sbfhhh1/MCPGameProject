# -*- coding: utf-8 -*-
import unreal, json
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pool = None
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break
om = pool.get_editor_property("OverrideMaterial") if pool else None
comps = pool.get_components_by_class(unreal.ProceduralMeshComponent) if pool else []
m0 = comps[0].get_material(0) if comps else None
white = unreal.EditorAssetLibrary.load_asset(
    "/Game/TransformationVFX/SM2SM/ChineseSeals/M_ChineseSeal_DefaultWhite")
r = {
    "override_material": om.get_path_name() if om else None,
    "comp0_material": m0.get_path_name() if m0 else None,
    "proc_count": len(comps),
    "white_mat_exists": bool(white),
}
unreal.log("[proc_mat] " + json.dumps(r, default=str))
