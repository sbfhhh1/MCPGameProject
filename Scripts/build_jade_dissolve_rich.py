import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
SRC_MASTER = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
ANCIENT = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"
NEW = f"{DIR}/M_Burst_JadeDissolve"
MI_NAMES = ["MI_Burst_Jade_YF", "MI_Burst_Jade_TYS", "MI_Burst_Jade_YZL"]


def scalar(mat, name, default, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", default)
    return e


# --- read ancient jade values to copy onto burst instances ---
ancient = unreal.load_asset(ANCIENT)
master = unreal.load_asset(SRC_MASTER)
anc_scalars = {str(n): mel.get_material_instance_scalar_parameter_value(ancient, n)
               for n in mel.get_scalar_parameter_names(ancient)}
anc_vectors = {str(n): mel.get_material_instance_vector_parameter_value(ancient, n)
               for n in mel.get_vector_parameter_names(ancient)}

# --- detach instances from old simplified material, then replace it ---
for name in MI_NAMES:
    mi = unreal.load_asset(f"{DIR}/{name}")
    if mi:
        mel.set_material_instance_parent(mi, master)
        mel.update_material_instance(mi)
        EAL.save_loaded_asset(mi)

if EAL.does_asset_exist(NEW):
    EAL.delete_asset(NEW)

mat = EAL.duplicate_asset(SRC_MASTER, NEW)
if not mat:
    raise RuntimeError("duplicate of YZL master failed")

# --- Translucent + Opacity 溶解（真正的 alpha 混合，在所有渲染路径都生效，绝不被当成不透明）---
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
try:
    mat.set_editor_property(
        "translucency_lighting_mode",
        unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
except Exception as _e:
    unreal.log_warning(f"[JadeRich] translucency lighting mode set failed: {_e}")

wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1300, 700)
tile = scalar(mat, "Dissolve Tile", 0.02, -1300, 860)
scaled = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1080, 720)
mel.connect_material_expressions(wp, "", scaled, "A")
mel.connect_material_expressions(tile, "", scaled, "B")

noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -880, 720)
noise.set_editor_property("scale", 1.0)
noise.set_editor_property("output_min", 0.0)
noise.set_editor_property("output_max", 1.0)
noise.set_editor_property("levels", 4)
try:
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX3D)
except Exception as _e:
    unreal.log_warning(f"[JadeRich] noise_function set failed: {_e}")
mel.connect_material_expressions(scaled, "", noise, "Position")

diss = scalar(mat, "Dissolve Amount", 1.0, -1080, 900)
inv = mel.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -900, 900)
mel.connect_material_expressions(diss, "", inv, "")
edge = scalar(mat, "Dissolve Edge", 0.35, -1080, 1020)
one = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -1080, 980)
one.set_editor_property("r", 1.0)
one_plus = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -900, 1000)
mel.connect_material_expressions(one, "", one_plus, "A")
mel.connect_material_expressions(edge, "", one_plus, "B")
t1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -720, 920)
mel.connect_material_expressions(inv, "", t1, "A")
mel.connect_material_expressions(one_plus, "", t1, "B")
threshold = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -560, 920)
mel.connect_material_expressions(t1, "", threshold, "A")
mel.connect_material_expressions(edge, "", threshold, "B")

thresh = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -400, 760)
mel.connect_material_expressions(noise, "", thresh, "A")
mel.connect_material_expressions(threshold, "", thresh, "B")
contrast = scalar(mat, "Dissolve Contrast", 3.0, -560, 1040)
sharp = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -240, 760)
mel.connect_material_expressions(thresh, "", sharp, "A")
mel.connect_material_expressions(contrast, "", sharp, "B")
sat = mel.create_material_expression(mat, unreal.MaterialExpressionSaturate, -80, 760)
mel.connect_material_expressions(sharp, "", sat, "")
# Translucent：把噪波溶解值接到 Opacity（不透明度），真 alpha 混合，溶解边缘清晰、所有渲染路径都生效。
mel.connect_material_property(sat, "", unreal.MaterialProperty.MP_OPACITY)

mel.recompile_material(mat)
EAL.save_loaded_asset(mat)
unreal.log("[JadeRich] M_Burst_JadeDissolve rebuilt from M_YZL_ProceduralJade_SSS + dissolve OpacityMask (19 jade params kept)")

# --- per-instance: inherit ancient jade look + subtle tint variance + Dissolve=1.0 ---
tint_variance = {
    "MI_Burst_Jade_YF": (unreal.LinearColor(0.20, 0.23, 0.07, 1.0), 0.18),
    "MI_Burst_Jade_TYS": (unreal.LinearColor(0.26, 0.21, 0.06, 1.0), 0.20),
    "MI_Burst_Jade_YZL": (unreal.LinearColor(0.127, 0.144, 0.033, 1.0), 0.0),
}
for name in MI_NAMES:
    mi = unreal.load_asset(f"{DIR}/{name}")
    if not mi:
        continue
    mel.set_material_instance_parent(mi, mat)
    for pname, pval in anc_scalars.items():
        mel.set_material_instance_scalar_parameter_value(mi, pname, pval)
    for pname, pval in anc_vectors.items():
        mel.set_material_instance_vector_parameter_value(mi, pname, pval)
    tint_color, tint_amount = tint_variance[name]
    mel.set_material_instance_vector_parameter_value(mi, "Master Tint", tint_color)
    mel.set_material_instance_scalar_parameter_value(mi, "Master Tint Amount", tint_amount)
    mel.set_material_instance_scalar_parameter_value(mi, "Dissolve Amount", 1.0)
    mel.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    unreal.log(f"[JadeRich] {name}: inherited ancient jade + tint variance, Dissolve=1.0")

unreal.log("[JadeRich] DONE")
