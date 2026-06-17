import unreal
LOG = "[VERIFY_JADE]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
def P(o):
    try: return o.get_name() if o else "None"
    except Exception: return str(o)
ell = unreal.EditorLevelLibrary
bp = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade")
actor = ell.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0,0,-400000))
if actor:
    sw = None
    for c in actor.get_components_by_class(unreal.ActorComponent):
        if "Switcher" in c.get_class().get_name():
            sw = c
    log("switcher = {}".format(sw.get_class().get_name() if sw else "NONE"))
    if sw:
        log("  particle_system = {}".format(P(sw.get_editor_property("particle_system"))))
        sfm = sw.get_editor_property("state_fade_materials")
        log("  state_fade_materials = [{}]".format(", ".join(P(x) for x in sfm)))
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property("static_mesh")
        log("  MESH '{}' = {}".format(c.get_name(), P(sm)))
    n = actor.get_component_by_class(unreal.NiagaraComponent)
    if n:
        log("  NIAGARA = {}".format(P(n.get_editor_property("asset"))))
    ell.destroy_actor(actor)
log("DONE")
