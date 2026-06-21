# -*- coding: utf-8 -*-
"""inspect BP_Burst_SM_Test 实例的 BurstSwitcher 组件关键属性(看今天的override)。"""
import unreal, json

LABEL = "BP_Burst_SM_Test"


def path_of(o):
    return o.get_path_name() if o else None


def main():
    actor = next((a for a in unreal.EditorLevelLibrary.get_all_level_actors()
                  if a.get_actor_label() == LABEL), None)
    if not actor:
        unreal.log("[burst_props] ACTOR_NOT_FOUND")
        return

    comp = None
    for c in actor.get_components_by_class(unreal.ActorComponent):
        if c.get_class().get_name() == "BurstMeshStateSwitcherComponent":
            comp = c
            break
    if not comp:
        unreal.log("[burst_props] COMPONENT_NOT_FOUND")
        return

    info = {}
    for prop in ["MorphParticleSystem", "StateFadeMaterials", "FallbackModelFadeMaterial",
                 "StateMeshes", "ModelFadeStartDissolve", "ModelFadeEndDissolve"]:
        try:
            v = comp.get_editor_property(prop)
            if isinstance(v, unreal.Array):
                info[prop] = [path_of(x) if hasattr(x, "get_path_name") else str(x) for x in v]
            elif hasattr(v, "get_path_name"):
                info[prop] = path_of(v)
            else:
                info[prop] = str(v)
        except Exception as e:
            info[prop] = "ERR:" + str(e)

    # 也看各 StaticMesh 组件当前材质
    mesh_mats = []
    for smc in actor.get_components_by_class(unreal.StaticMeshComponent):
        mats = [path_of(smc.get_material(i)) for i in range(smc.get_num_materials())]
        mesh_mats.append({smc.get_name(): mats})
    info["mesh_component_materials"] = mesh_mats

    unreal.log("[burst_props] " + json.dumps(info, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
