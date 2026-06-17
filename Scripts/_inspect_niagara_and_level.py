import unreal

LOG = "[NIAG_LVL]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
ar = unreal.AssetRegistryHelpers.get_asset_registry()

# 1. Niagara 文件夹
log("--- Niagara systems ---")
for a in unreal.EditorAssetLibrary.list_assets("/Game/TransformationVFX/Niagara", recursive=True, include_folder=False):
    data = ar.get_asset_by_object_path(a)
    cls = str(data.asset_class_path.asset_name) if data else "?"
    if cls == "NiagaraSystem":
        log("  NS {}".format(a))

# 2. BP_Return_SM 的 Niagara：spawn 后读 construction 之后的 asset + 看 BP 变量默认
ell = unreal.EditorLevelLibrary
bp = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/BP/Examples/BP_Return_SM")
actor = ell.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0,0,-200000))
if actor:
    ncomp = actor.get_component_by_class(unreal.NiagaraComponent)
    if ncomp:
        asset = ncomp.get_editor_property("asset")
        log("  BP_Return_SM live niagara = {}".format(asset.get_path_name() if asset else "None"))
    ell.destroy_actor(actor)

# 3. SM2SM 关卡里的 actor（通过加载世界包，遍历）
log("--- SM2SM level actors ---")
lvl_path = "/Game/TransformationVFX/SM2SM/SM2SM"
try:
    world = unreal.EditorAssetLibrary.load_asset(lvl_path)
    log("  loaded world asset = {} ({})".format(world.get_name() if world else "None", type(world).__name__))
    # 读取 PersistentLevel 的 actors
    if world:
        persistent = world.get_editor_property("persistent_level")
        actors = persistent.get_editor_property("actors") if persistent else None
        if actors:
            log("  actor entries = {}".format(len(actors)))
            for a in actors:
                if not a:
                    continue
                cls = a.get_class().get_name()
                label = ""
                try:
                    label = a.get_actor_label()
                except Exception:
                    label = a.get_name()
                mesh = ""
                try:
                    smc = a.get_component_by_class(unreal.StaticMeshComponent)
                    if smc and smc.static_mesh:
                        mesh = " mesh={}".format(smc.static_mesh.get_name())
                except Exception:
                    pass
                # 是否含切换组件
                sw = ""
                try:
                    for c in a.get_components_by_class(unreal.ActorComponent):
                        if "Switcher" in c.get_class().get_name():
                            sw = " SWITCHER={}".format(c.get_class().get_name())
                except Exception:
                    pass
                log("  LVLACTOR '{}' [{}]{}{}".format(label, cls, mesh, sw))
except Exception as e:
    log("  level read error: {}".format(e))

log("DONE")
