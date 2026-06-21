# -*- coding: utf-8 -*-
"""客观核对 pool 实际状态：组件类型、用的网格、三角形数；以及资产是否 join 版新网格。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_verify_pool_state.json"


def main():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pool = None
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() == "ChineseSealPoolAnimator":
            pool = a
            break

    result = {}
    if pool:
        sm = pool.get_components_by_class(unreal.StaticMeshComponent)
        pm = pool.get_components_by_class(unreal.ProceduralMeshComponent)
        result["pool_label"] = pool.get_actor_label()
        result["static_components"] = len(sm)
        result["procedural_components"] = len(pm)
        if sm:
            mesh = sm[0].get_editor_property("static_mesh")
            result["first_comp_mesh"] = mesh.get_name() if mesh else None
            if mesh and hasattr(mesh, "get_num_triangles"):
                result["first_comp_tris"] = mesh.get_num_triangles(0)
    else:
        result["pool"] = "NOT FOUND"

    # 直接查资产三角形数（join 版 Shui 约 7929 polys -> 三角化后更多）
    asset = unreal.EditorAssetLibrary.load_asset(
        "/Game/TransformationVFX/SM2SM/ChineseSeals/SM_Seal_Shui.SM_Seal_Shui")
    if asset and hasattr(asset, "get_num_triangles"):
        result["asset_SM_Seal_Shui_tris"] = asset.get_num_triangles(0)
        result["asset_SM_Seal_Shui_verts"] = asset.get_num_vertices(0) if hasattr(asset, "get_num_vertices") else None

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[verify_pool_state] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
