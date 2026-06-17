import unreal

LOG = "[INSPECT_RETURN]"

def log(msg):
    unreal.log_warning("{} {}".format(LOG, msg))

# 1. 当前关卡
try:
    world = unreal.EditorLevelLibrary.get_editor_world()
    log("CURRENT_LEVEL = {}".format(world.get_path_name() if world else "None"))
except Exception as e:
    log("level error: {}".format(e))

# 2. 列出关卡里所有 actor（重点找玉石/jade/yzl/static mesh）
try:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    log("ACTOR_COUNT = {}".format(len(actors)))
    for a in actors:
        label = a.get_actor_label()
        cls = a.get_class().get_name()
        # 静态网格信息
        mesh_info = ""
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            sm = smc.static_mesh
            if sm:
                mesh_info = " mesh={}".format(sm.get_path_name())
                mats = smc.get_materials()
                mat_names = [m.get_path_name() if m else "None" for m in mats]
                mesh_info += " mats={}".format(mat_names)
        log("ACTOR label='{}' class={}{}".format(label, cls, mesh_info))
except Exception as e:
    log("actors error: {}".format(e))

# 3. 检查 BP_Return_SM 是否存在
ret_path = "/Game/TransformationVFX/BP/Examples/BP_Return_SM"
try:
    exists = unreal.EditorAssetLibrary.does_asset_exist(ret_path)
    log("BP_Return_SM exists = {}".format(exists))
    if exists:
        bp = unreal.EditorAssetLibrary.load_asset(ret_path)
        log("BP_Return_SM class = {}".format(bp.get_class().get_name()))
        # 列出 SCS 组件
        try:
            gen_class = bp.generated_class()
            cdo = unreal.get_default_object(gen_class)
            log("CDO = {}".format(cdo.get_name() if cdo else "None"))
        except Exception as e2:
            log("cdo error: {}".format(e2))
except Exception as e:
    log("return bp error: {}".format(e))

log("DONE")
