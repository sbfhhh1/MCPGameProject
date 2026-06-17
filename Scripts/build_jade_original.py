import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
SRC = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
ANCIENT = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"
NEW = f"{DIR}/M_Burst_JadeFinal"
MI_NAMES = ["MI_Burst_Jade_YF", "MI_Burst_Jade_TYS", "MI_Burst_Jade_YZL"]


def scalar(mat, n, d, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", n)
    e.set_editor_property("default_value", d)
    return e


# 读古玉参数值
ancient = unreal.load_asset(ANCIENT)
anc_s = {str(n): mel.get_material_instance_scalar_parameter_value(ancient, n)
         for n in mel.get_scalar_parameter_names(ancient)}
anc_v = {str(n): mel.get_material_instance_vector_parameter_value(ancient, n)
         for n in mel.get_vector_parameter_names(ancient)}

# 复制最初玉石主材质（保留全部 19 参数和外观）到新名字，避免删除被引用资产
if EAL.does_asset_exist(NEW):
    EAL.delete_asset(NEW)
mat = EAL.duplicate_asset(SRC, NEW)
if not mat:
    raise RuntimeError("duplicate M_YZL failed")

# 改 Translucent（真半透明 alpha，游戏渲染必生效）。着色用 DefaultLit——
# Subsurface+Translucent 是无效组合会让编辑器崩溃；玉石的通透感靠原材质的 Edge Transmission 边缘透光 + 半透体现。
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
try:
    mat.set_editor_property("translucency_lighting_mode",
                            unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
except Exception as e:
    unreal.log_warning(f"[JadeOrig] lighting mode {e}")

# 加 3D 噪波溶解 → Opacity（不动原有玉石节点）
wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1400, 800)
tile = scalar(mat, "Dissolve Tile", 0.08, -1400, 940)
scaled = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1180, 820)
mel.connect_material_expressions(wp, "", scaled, "A")
mel.connect_material_expressions(tile, "", scaled, "B")
noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -980, 820)
noise.set_editor_property("output_min", 0.0)
noise.set_editor_property("output_max", 1.0)
noise.set_editor_property("levels", 4)
try:
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX3D)
except Exception:
    pass
mel.connect_material_expressions(scaled, "", noise, "Position")
diss = scalar(mat, "Dissolve Amount", 1.0, -1180, 980)
inv = mel.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -980, 980)
mel.connect_material_expressions(diss, "", inv, "")
edge = scalar(mat, "Dissolve Edge", 0.1, -1180, 1100)
onec = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -1180, 1060)
onec.set_editor_property("r", 1.0)
onep = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -980, 1080)
mel.connect_material_expressions(onec, "", onep, "A")
mel.connect_material_expressions(edge, "", onep, "B")
t1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -800, 1000)
mel.connect_material_expressions(inv, "", t1, "A")
mel.connect_material_expressions(onep, "", t1, "B")
thr = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -620, 1000)
mel.connect_material_expressions(t1, "", thr, "A")
mel.connect_material_expressions(edge, "", thr, "B")
sub = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -440, 840)
mel.connect_material_expressions(noise, "", sub, "A")
mel.connect_material_expressions(thr, "", sub, "B")
con = scalar(mat, "Dissolve Contrast", 2.0, -620, 1120)
shp = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -240, 840)
mel.connect_material_expressions(sub, "", shp, "A")
mel.connect_material_expressions(con, "", shp, "B")
sat = mel.create_material_expression(mat, unreal.MaterialExpressionSaturate, -60, 840)
mel.connect_material_expressions(shp, "", sat, "")
mel.connect_material_property(sat, "", unreal.MaterialProperty.MP_OPACITY)

mel.recompile_material(mat)
EAL.save_loaded_asset(mat)
unreal.log("[JadeOrig] original jade material (19 params) + Translucent opacity dissolve")

# 三个 MI 改父材质 = 这个原玉石溶解材质，继承古玉参数值 + 微调色差 + Dissolve=1
tint = {
    "MI_Burst_Jade_YF": (unreal.LinearColor(0.20, 0.23, 0.07, 1.0), 0.18),
    "MI_Burst_Jade_TYS": (unreal.LinearColor(0.26, 0.21, 0.06, 1.0), 0.20),
    "MI_Burst_Jade_YZL": (unreal.LinearColor(0.127, 0.144, 0.033, 1.0), 0.0),
}
for n in MI_NAMES:
    mi = unreal.load_asset(f"{DIR}/{n}")
    if not mi:
        continue
    mel.set_material_instance_parent(mi, mat)
    for pn, pv in anc_s.items():
        mel.set_material_instance_scalar_parameter_value(mi, pn, pv)
    for pn, pv in anc_v.items():
        mel.set_material_instance_vector_parameter_value(mi, pn, pv)
    tc, ta = tint[n]
    mel.set_material_instance_vector_parameter_value(mi, "Master Tint", tc)
    mel.set_material_instance_scalar_parameter_value(mi, "Master Tint Amount", ta)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Amount", 1.0)
    mel.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    unreal.log(f"[JadeOrig] {n} reparented to original jade + dissolve")

unreal.log("[JadeOrig] DONE")
