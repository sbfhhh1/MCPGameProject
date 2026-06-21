# -*- coding: utf-8 -*-
"""精确统计印章 actor：内部唯一名 + 网格 + 位置，检测重复。只查不删。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_check_seal_dupes.json"


def main():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    seals = []
    pool = []
    for a in sub.get_all_level_actors():
        cls = a.get_class().get_name()
        label = a.get_actor_label()
        if cls == "ChineseSealPoolAnimator":
            pm = len(a.get_components_by_class(unreal.ProceduralMeshComponent))
            sm = len(a.get_components_by_class(unreal.StaticMeshComponent))
            pool.append({"name": a.get_name(), "label": label, "proc": pm, "static": sm})
            continue
        comps = a.get_components_by_class(unreal.StaticMeshComponent)
        mesh_name = None
        for c in comps:
            m = c.get_editor_property("static_mesh")
            if m and m.get_name().startswith("SM_Seal_"):
                mesh_name = m.get_name()
        if mesh_name:
            loc = a.get_actor_location()
            seals.append({
                "name": a.get_name(),
                "label": label,
                "mesh": mesh_name,
                "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            })

    # 按网格分组检测重复
    by_mesh = {}
    for s in seals:
        by_mesh.setdefault(s["mesh"], []).append(s)
    dupes = {k: v for k, v in by_mesh.items() if len(v) > 1}

    result = {
        "seal_actor_count": len(seals),
        "unique_meshes": list(by_mesh.keys()),
        "duplicates": dupes,
        "pool_actors": pool,
        "all_seals": seals,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[check_seal_dupes] seals=%d dupes=%d" % (len(seals), len(dupes)))


if __name__ == "__main__":
    main()
