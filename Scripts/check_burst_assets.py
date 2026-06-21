# -*- coding: utf-8 -*-
"""检查玉石材质有无 Dissolve Amount 参数 + Vortex 粒子是否存在。"""
import unreal, json

MATS = [
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YF_Jade_TYS_SSS",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_TYS_SSS",
    "/Game/TransformationVFX/Material/ObjectMaterial/MI_Chair_UniversalDissolve",
]
PARTICLES = [
    "/Game/TransformationVFX/SM2SM/jude/P_Morph_5_SM_Vortex",
    "/Game/NiagaraMorphEffect/Niagara/P_Morph_5_SM",
]


def main():
    info = {"materials": [], "particles": []}
    for p in MATS:
        m = unreal.EditorAssetLibrary.load_asset(p)
        entry = {"path": p.split("/")[-1], "exists": bool(m)}
        if m and isinstance(m, unreal.MaterialInstance):
            try:
                val = m.get_scalar_parameter_value("Dissolve Amount")
                entry["has_DissolveAmount"] = True
                entry["value"] = val
            except Exception:
                entry["has_DissolveAmount"] = False
        info["materials"].append(entry)
    for p in PARTICLES:
        exists = unreal.EditorAssetLibrary.does_asset_exist(p)
        info["particles"].append({"path": p.split("/")[-1], "exists": exists})
    unreal.log("[burst_assets] " + json.dumps(info, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
