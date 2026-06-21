# -*- coding: utf-8 -*-
"""彻底审计关卡所有 actor：label/class/位置/网格组件/用的网格名。不遗漏。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_audit_all_actors.json"


def main():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    items = []
    for a in actors:
        loc = a.get_actor_location()
        smc = a.get_components_by_class(unreal.StaticMeshComponent)
        pmc = a.get_components_by_class(unreal.ProceduralMeshComponent)
        # 收集静态网格用的网格名（去重）
        mesh_names = []
        for c in smc:
            m = c.get_editor_property("static_mesh")
            if m:
                mesh_names.append(m.get_name())
        distinct = sorted(set(mesh_names))
        items.append({
            "label": a.get_actor_label(),
            "name": a.get_name(),
            "class": a.get_class().get_name(),
            "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "static_comp": len(smc),
            "proc_comp": len(pmc),
            "distinct_mesh_count": len(distinct),
            "distinct_meshes": distinct[:25],
        })
    result = {"total": len(actors), "actors": items}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[audit] total=%d" % len(actors))


if __name__ == "__main__":
    main()
