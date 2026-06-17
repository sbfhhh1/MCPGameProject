import unreal

LOG = "[SPAWN_INS]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))

ell = unreal.EditorLevelLibrary

def inspect(bp_path):
    log("==== {} ====".format(bp_path))
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    gen = bp.generated_class()
    actor = ell.spawn_actor_from_class(gen, unreal.Vector(0,0,-100000), unreal.Rotator(0,0,0))
    if not actor:
        log("  spawn failed")
        return
    try:
        comps = actor.get_components_by_class(unreal.ActorComponent)
        log("  comp count = {}".format(len(comps)))
        for c in comps:
            cls = c.get_class().get_name()
            extra = ""
            if "Niagara" in cls:
                try:
                    asset = c.get_editor_property("asset")
                    extra = " NIAGARA={}".format(asset.get_path_name() if asset else "None")
                except Exception as e:
                    extra = " niag_err={}".format(e)
            if cls == "StaticMeshComponent":
                try:
                    sm = c.get_editor_property("static_mesh")
                    extra = " MESH={}".format(sm.get_path_name() if sm else "None")
                except Exception:
                    pass
            log("  COMP '{}' [{}]{}".format(c.get_name(), cls, extra))
        # 列出 Niagara 用户参数
        ncomp = actor.get_component_by_class(unreal.NiagaraComponent)
        if ncomp:
            asset = ncomp.get_editor_property("asset")
            if asset:
                try:
                    exposed = unreal.NiagaraSystem.cast(asset)
                    # 读取 user parameter names via override params not directly exposed; try get_exposed_parameters
                    log("  NIAGARA_ASSET_PATH={}".format(asset.get_path_name()))
                except Exception as e:
                    log("  niag asset cast err {}".format(e))
    finally:
        ell.destroy_actor(actor)

inspect("/Game/TransformationVFX/BP/Examples/BP_Return_SM")
inspect("/Game/TransformationVFX/BP/Examples/BP_Burst_SM")
log("DONE")
