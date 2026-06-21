import json, unreal
OUT = r"C:/UE_Project/MCPGameProject/Scripts/_terrain_dbg.json"
data = {"found": False}
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if actor.get_actor_label() != "Terrace_Terrain":
            continue
    except Exception:
        continue
    # 挪到画框前方，强制默认材质排查
    actor.set_actor_location(unreal.Vector(-50.0, 0.0, 160.0), False, False)
    runtime = actor.get_component_by_class(unreal.BlenderGeometryNodesComponent)
    comps = [c.get_class().get_name() for c in actor.get_components_by_class(unreal.ActorComponent)]
    pmc = actor.get_component_by_class(unreal.ProceduralMeshComponent)
    data = {"found": True, "components": comps}
    if pmc:
        data["pmc_visible"] = pmc.is_visible()
        data["pmc_sections"] = pmc.get_num_sections()
        data["pmc_num_materials"] = pmc.get_num_materials()
        mat0 = pmc.get_material(0)
        data["pmc_mat0"] = mat0.get_name() if mat0 else None
    o, e = actor.get_actor_bounds(False)
    data["bounds_origin"] = [o.x, o.y, o.z]
    data["bounds_extent"] = [e.x, e.y, e.z]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    unreal.log("[debug_terrain_render] " + json.dumps(data))
    break
else:
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
