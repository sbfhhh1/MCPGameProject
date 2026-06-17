import unreal

LOG = "[INSPECT_PS]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))

def dump_bp_scs(bp_path):
    log("==== BP {} ====".format(bp_path))
    if not unreal.EditorAssetLibrary.does_asset_exist(bp_path):
        log("  NOT FOUND")
        return
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    try:
        gen = bp.generated_class()
        cdo = unreal.get_default_object(gen)
        # 遍历 components via SimpleConstructionScript
        # 用 get_actor's components by spawning is heavy; instead read SCS nodes
        scs = bp.get_editor_property("simple_construction_script") if False else None
    except Exception as e:
        log("  gen error: {}".format(e))
    # 用 subobject 方式读取 component 模板
    try:
        gen = bp.generated_class()
        cdo = unreal.get_default_object(gen)
        comps = cdo.get_components_by_class(unreal.ActorComponent)
        log("  CDO comp count = {}".format(len(comps)))
        for c in comps:
            cls = c.get_class().get_name()
            extra = ""
            # Niagara
            if "Niagara" in cls:
                try:
                    asset = c.get_editor_property("asset")
                    extra = " NIAGARA_SYSTEM={}".format(asset.get_path_name() if asset else "None")
                except Exception as e:
                    extra = " (niagara asset read err {})".format(e)
            # Cascade ParticleSystem
            if cls == "ParticleSystemComponent":
                try:
                    tmpl = c.get_editor_property("template")
                    extra = " CASCADE_TEMPLATE={}".format(tmpl.get_path_name() if tmpl else "None")
                except Exception as e:
                    extra = " (cascade read err {})".format(e)
            if cls == "StaticMeshComponent":
                try:
                    sm = c.get_editor_property("static_mesh")
                    extra = " MESH={}".format(sm.get_path_name() if sm else "None")
                except Exception:
                    pass
            log("  COMP {} [{}]{}".format(c.get_name(), cls, extra))
    except Exception as e:
        log("  comp dump error: {}".format(e))

dump_bp_scs("/Game/TransformationVFX/BP/Examples/BP_Return_SM")
dump_bp_scs("/Game/TransformationVFX/BP/Examples/BP_Burst_SM")

# 找 BurstMeshStateSwitcher C++ 类
log("--- find switcher class ---")
for cname in ["BurstMeshStateSwitcherComponent", "BurstMeshStateSwitcher"]:
    try:
        c = unreal.find_class(cname)
        log("  class {} = {}".format(cname, c))
    except Exception as e:
        log("  class {} err {}".format(cname, e))

# 搜索所有 /Game 蓝图里名字含 burst/jade/switch/return 的
log("--- search custom BPs ---")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
allg = unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
for a in allg:
    low = a.lower()
    data = ar.get_asset_by_object_path(a)
    cls = str(data.asset_class_path.asset_name) if data else "?"
    if cls == "Blueprint" and any(k in low for k in ["burst","jade","switch","return","sm2sm","yzl"]):
        log("  CUSTOM_BP {}".format(a))

log("DONE")
