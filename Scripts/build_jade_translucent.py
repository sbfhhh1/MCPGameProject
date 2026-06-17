import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
NEW = f"{DIR}/M_Burst_JadeDissolve"


def scalar(mat, n, d, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", n)
    e.set_editor_property("default_value", d)
    return e


def vector(mat, n, v, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", n)
    e.set_editor_property("default_value", v)
    return e


if EAL.does_asset_exist(NEW):
    mat = unreal.load_asset(NEW)
    mel.delete_all_material_expressions(mat)
else:
    mat = tools.create_asset("M_Burst_JadeDissolve", DIR, unreal.Material, unreal.MaterialFactoryNew())

mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
mat.set_editor_property("two_sided", True)
try:
    mat.set_editor_property("translucency_lighting_mode",
                            unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
except Exception as e:
    unreal.log_warning(f"[JadeTrans] lighting mode {e}")

# --- jade appearance ---
body = vector(mat, "Jade Body Color", unreal.LinearColor(0.14, 0.34, 0.15, 1.0), -700, -300)
mel.connect_material_property(body, "", unreal.MaterialProperty.MP_BASE_COLOR)
rough = scalar(mat, "Jade Roughness", 0.2, -700, -180)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
spec = scalar(mat, "Jade Specular", 0.7, -700, -100)
mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

# fresnel rim emissive = jade translucency glow (fake SSS look)
fres = mel.create_material_expression(mat, unreal.MaterialExpressionFresnel, -700, 80)
glow = scalar(mat, "Jade Glow", 1.2, -700, 200)
scat = vector(mat, "Jade Scatter Color", unreal.LinearColor(0.30, 0.62, 0.26, 1.0), -700, 300)
em1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, 120)
mel.connect_material_expressions(fres, "", em1, "A")
mel.connect_material_expressions(glow, "", em1, "B")
em2 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, 160)
mel.connect_material_expressions(em1, "", em2, "A")
mel.connect_material_expressions(scat, "", em2, "B")
mel.connect_material_property(em2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# --- opacity = 3D noise dissolve (translucent alpha, renders everywhere) ---
wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1400, 560)
tile = scalar(mat, "Dissolve Tile", 0.08, -1400, 700)
scaled = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1180, 580)
mel.connect_material_expressions(wp, "", scaled, "A")
mel.connect_material_expressions(tile, "", scaled, "B")
noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -980, 580)
noise.set_editor_property("output_min", 0.0)
noise.set_editor_property("output_max", 1.0)
noise.set_editor_property("levels", 4)
try:
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX3D)
except Exception:
    pass
mel.connect_material_expressions(scaled, "", noise, "Position")

diss = scalar(mat, "Dissolve Amount", 1.0, -1180, 760)
inv = mel.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -980, 760)
mel.connect_material_expressions(diss, "", inv, "")
edge = scalar(mat, "Dissolve Edge", 0.1, -1180, 880)
onec = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -1180, 840)
onec.set_editor_property("r", 1.0)
onep = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -980, 860)
mel.connect_material_expressions(onec, "", onep, "A")
mel.connect_material_expressions(edge, "", onep, "B")
t1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -800, 780)
mel.connect_material_expressions(inv, "", t1, "A")
mel.connect_material_expressions(onep, "", t1, "B")
thr = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -620, 780)
mel.connect_material_expressions(t1, "", thr, "A")
mel.connect_material_expressions(edge, "", thr, "B")
sub = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -440, 600)
mel.connect_material_expressions(noise, "", sub, "A")
mel.connect_material_expressions(thr, "", sub, "B")
con = scalar(mat, "Dissolve Contrast", 2.0, -620, 900)
shp = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -240, 600)
mel.connect_material_expressions(sub, "", shp, "A")
mel.connect_material_expressions(con, "", shp, "B")
sat = mel.create_material_expression(mat, unreal.MaterialExpressionSaturate, -60, 600)
mel.connect_material_expressions(shp, "", sat, "")
mel.connect_material_property(sat, "", unreal.MaterialProperty.MP_OPACITY)

mel.recompile_material(mat)
EAL.save_loaded_asset(mat)
unreal.log("[JadeTrans] material rebuilt: Translucent + Opacity noise dissolve")

variants = {
    "MI_Burst_Jade_YF": unreal.LinearColor(0.16, 0.36, 0.16, 1.0),
    "MI_Burst_Jade_TYS": unreal.LinearColor(0.22, 0.34, 0.13, 1.0),
    "MI_Burst_Jade_YZL": unreal.LinearColor(0.13, 0.32, 0.14, 1.0),
}
for n, col in variants.items():
    mi = unreal.load_asset(f"{DIR}/{n}")
    if not mi:
        continue
    mel.set_material_instance_parent(mi, mat)
    mel.set_material_instance_vector_parameter_value(mi, "Jade Body Color", col)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Amount", 1.0)
    mel.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    unreal.log(f"[JadeTrans] {n} reparented")

unreal.log("[JadeTrans] DONE")
