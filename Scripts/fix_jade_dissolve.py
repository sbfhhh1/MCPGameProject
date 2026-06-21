# -*- coding: utf-8 -*-
"""把玉石材质的 Dissolve Amount 设回 1.0(实体可见)。1.0=完整, 0.0=消散透明。"""
import unreal, json

MATS = [
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YF_Jade_TYS_SSS",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_TYS_SSS",
]

results = []
for p in MATS:
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        results.append({"path": p, "ok": False, "reason": "not found"})
        continue
    before = None
    try:
        before = m.get_scalar_parameter_value("Dissolve Amount")
    except Exception:
        pass
    ok = unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m, "Dissolve Amount", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    after = m.get_scalar_parameter_value("Dissolve Amount")
    results.append({"path": p.split("/")[-1], "set_ok": ok, "before": before, "after": after})

unreal.log("[fix_jade] " + json.dumps(results, default=str))
