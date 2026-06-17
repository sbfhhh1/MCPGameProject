import unreal

LOG = "[DUMP_MESH]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
ell = unreal.EditorLevelLibrary
def P(o):
    try: return o.get_path_name() if o else "None"
    except Exception: return str(o)

bp = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/BP/Examples/BP_Burst_SM")
actor = ell.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0,0,-300000))
if actor:
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        try:
            name = c.get_name()
            sm = c.get_editor_property("static_mesh")
            loc = c.get_editor_property("relative_location")
            rot = c.get_editor_property("relative_rotation")
            scl = c.get_editor_property("relative_scale3d")
            try:
                mats = [P(m) for m in c.get_materials()]
            except Exception:
                mats = ["<err>"]
            log("'{}' mesh={} loc=({:.1f},{:.1f},{:.1f}) rot=(p{:.1f},y{:.1f},r{:.1f}) scl=({:.3f},{:.3f},{:.3f}) mats={}".format(
                name, P(sm), loc.x,loc.y,loc.z, rot.pitch,rot.yaw,rot.roll, scl.x,scl.y,scl.z, mats))
        except Exception as e:
            log("comp err {}".format(e))
    n = actor.get_component_by_class(unreal.NiagaraComponent)
    if n:
        try:
            loc=n.get_editor_property("relative_location"); scl=n.get_editor_property("relative_scale3d")
            log("NIAGARA '{}' asset={} loc=({:.1f},{:.1f},{:.1f}) scl=({:.3f},{:.3f},{:.3f})".format(
                n.get_name(), P(n.get_editor_property("asset")), loc.x,loc.y,loc.z, scl.x,scl.y,scl.z))
        except Exception as e:
            log("niag err {}".format(e))
    ell.destroy_actor(actor)
log("DONE")
