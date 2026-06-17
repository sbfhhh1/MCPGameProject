import unreal

LOG = "[DUMP_CFG]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
ell = unreal.EditorLevelLibrary

bp = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/BP/Examples/BP_Burst_SM")
actor = ell.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0,0,-300000))

def pathOf(o):
    try:
        return o.get_path_name() if o else "None"
    except Exception:
        return str(o)

if actor:
    # 找切换组件
    comp = None
    for c in actor.get_components_by_class(unreal.ActorComponent):
        if "Switcher" in c.get_class().get_name():
            comp = c
            break
    if comp:
        log("=== SWITCHER {} ===".format(comp.get_class().get_name()))
        props = ["particle_system","particle_material","fallback_model_fade_material",
                 "front_half_duration","model_fade_in_duration","source_hide_delay",
                 "particle_model_overlap_duration","source_fade_out_duration",
                 "particle_effect_scale","inhalation_spread_scale","particle_non_uniform_scale",
                 "particle_location_offset","particle_rotation_offset","attractor_position",
                 "b_use_state_particle_materials","particle_current_mode",
                 "initial_transformation_alpha","first_half_end_transformation_alpha",
                 "transformation_alpha_ease_exponent","b_use_natural_particle_fade_out",
                 "particle_fade_out_duration","particle_fade_out_ease_exponent",
                 "particle_fade_opacity_parameter","model_fade_start_dissolve","model_fade_end_dissolve"]
        for p in props:
            try:
                v = comp.get_editor_property(p)
                if hasattr(v, "get_path_name"):
                    v = v.get_path_name()
                log("  {} = {}".format(p, v))
            except Exception as e:
                log("  {} ERR {}".format(p, e))
        # 数组材质
        for arr in ["state_fade_materials","state_particle_materials"]:
            try:
                v = comp.get_editor_property(arr)
                log("  {} = [{}]".format(arr, ", ".join(pathOf(x) for x in v)))
            except Exception as e:
                log("  {} ERR {}".format(arr, e))
    else:
        log("no switcher comp found")

    # 三个网格组件 transform + 材质
    log("=== MESH COMPONENTS ===")
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        name = c.get_name()
        sm = c.get_editor_property("static_mesh")
        loc = c.get_relative_location()
        rot = c.get_relative_rotation()
        scl = c.get_relative_scale3d()
        vis = c.is_visible()
        mats = [pathOf(m) for m in c.get_materials()]
        log("  '{}' mesh={} loc={} rot={} scl={} vis={} mats={}".format(
            name, pathOf(sm), loc, rot, scl, vis, mats))
    # niagara transform
    n = actor.get_component_by_class(unreal.NiagaraComponent)
    if n:
        log("  NIAGARA '{}' asset={} loc={} rot={} scl={}".format(
            n.get_name(), pathOf(n.get_editor_property("asset")),
            n.get_relative_location(), n.get_relative_rotation(), n.get_relative_scale3d()))
    ell.destroy_actor(actor)
else:
    log("spawn failed")
log("DONE")
