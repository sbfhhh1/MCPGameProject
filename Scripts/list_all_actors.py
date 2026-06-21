# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_list_all_actors.json"


def main():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    items = []
    for a in actors:
        loc = a.get_actor_location()
        comps = a.get_components_by_class(unreal.MeshComponent)
        comp_classes = {}
        meshes = []
        for c in comps:
            cn = c.get_class().get_name()
            comp_classes[cn] = comp_classes.get(cn, 0) + 1
            if isinstance(c, unreal.StaticMeshComponent):
                m = c.get_editor_property("static_mesh")
                if m:
                    meshes.append(m.get_name())
        items.append({
            "label": a.get_actor_label(),
            "class": a.get_class().get_name(),
            "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "mesh_components": comp_classes,
            "static_meshes": meshes[:4],
        })
    result = {"total": len(actors), "actors": items}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[list_all_actors] total=%d" % len(actors))


if __name__ == "__main__":
    main()
