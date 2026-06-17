import unreal
LOG="[JMAT]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

MATS=[
 "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade",
 "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS",
 "/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve",
 "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve",
 "/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeSSS",
 "/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve",
 "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YF",
]

def base_mat(m):
    cur=m
    for _ in range(6):
        if isinstance(cur, unreal.MaterialInstance):
            p=cur.get_editor_property("parent")
            if p: cur=p; continue
        break
    return cur

for path in MATS:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        log("MISSING {}".format(path)); continue
    m = unreal.EditorAssetLibrary.load_asset(path)
    cls = m.get_class().get_name()
    bm = base_mat(m)
    try:
        blend = bm.get_editor_property("blend_mode")
        shading = bm.get_editor_property("shading_model")
    except Exception as e:
        blend="?"; shading="?({})".format(e)
    line="{} [{}] base={} blend={} shading={}".format(path.split('/')[-1], cls, bm.get_name(), blend, shading)
    # 查 Dissolve Amount + Jade Body Color
    for pn in ["Dissolve Amount"]:
        try:
            v = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(m, pn) if isinstance(m,unreal.MaterialInstance) else unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(bm, pn)
            line += " | {}={}".format(pn, v)
        except Exception as e:
            line += " | {}=ERR".format(pn)
    log(line)
log("DONE")
