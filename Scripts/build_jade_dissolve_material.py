import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

ASSET_DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
MAT_NAME = "M_Burst_JadeDissolve"
MAT_PATH = f"{ASSET_DIR}/{MAT_NAME}"
NOISE = "/Game/TransformationVFX/Texture/T_Perlin_Noise"


def scalar(mat, name, default, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", default)
    return e


def vector(mat, name, value, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", value)
    return e


# create or load (idempotent rebuild)
if EAL.does_asset_exist(MAT_PATH):
    mat = unreal.load_asset(MAT_PATH)
    mel.delete_all_material_expressions(mat)
else:
    mat = tools.create_asset(MAT_NAME, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())

mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
mat.set_editor_property("two_sided", False)
mat.set_editor_property("opacity_mask_clip_value", 0.333)

# --- jade appearance ---
jade_color = vector(mat, "Jade Color", unreal.LinearColor(0.25, 0.32, 0.10, 1.0), -700, -360)
mel.connect_material_property(jade_color, "", unreal.MaterialProperty.MP_BASE_COLOR)
scatter = vector(mat, "Jade Scatter Color", unreal.LinearColor(0.34, 0.42, 0.15, 1.0), -700, -240)
mel.connect_material_property(scatter, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
rough = scalar(mat, "Jade Roughness", 0.18, -700, -120)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
spec = scalar(mat, "Jade Specular", 0.65, -700, -20)
mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 70)
metal.set_editor_property("r", 0.0)
mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)

# --- world-space 3D procedural noise dissolve (no streaking, UV-independent) ---
# 用真 3D 梯度噪波按世界坐标采样，避免旧版只取 xy 投影沿 z 拉成条纹的问题，
# 观感接近椅子原始案例的噪波溶解。
wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1300, 260)
tile = scalar(mat, "Dissolve Tile", 0.05, -1300, 440)
scaled = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1080, 300)
mel.connect_material_expressions(wp, "", scaled, "A")
mel.connect_material_expressions(tile, "", scaled, "B")

noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -880, 300)
noise.set_editor_property("scale", 1.0)
noise.set_editor_property("output_min", 0.0)
noise.set_editor_property("output_max", 1.0)
noise.set_editor_property("levels", 4)
try:
    noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX3D)
except Exception as _e:
    unreal.log_warning(f"[JadeBuild] noise_function set failed: {_e}")
mel.connect_material_expressions(scaled, "", noise, "Position")

# Remapped threshold so endpoints are CLEAN (no leftover holes / no premature pop):
#   threshold = (1 - Dissolve) * (1 + Edge) - Edge
#   Dissolve=1 -> threshold = -Edge  => noise - (-Edge) = noise+Edge > 0 everywhere => FULLY visible, no holes
#   Dissolve=0 -> threshold =  1     => noise - 1 <= 0 everywhere => fully dissolved away
diss = scalar(mat, "Dissolve Amount", 1.0, -900, 480)
inv = mel.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -740, 480)
mel.connect_material_expressions(diss, "", inv, "")

edge = scalar(mat, "Dissolve Edge", 0.2, -900, 640)
one = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -900, 580)
one.set_editor_property("r", 1.0)
one_plus = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -740, 600)
mel.connect_material_expressions(one, "", one_plus, "A")
mel.connect_material_expressions(edge, "", one_plus, "B")
t1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -560, 500)
mel.connect_material_expressions(inv, "", t1, "A")
mel.connect_material_expressions(one_plus, "", t1, "B")
threshold = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -420, 500)
mel.connect_material_expressions(t1, "", threshold, "A")
mel.connect_material_expressions(edge, "", threshold, "B")

thresh = mel.create_material_expression(mat, unreal.MaterialExpressionSubtract, -260, 360)
mel.connect_material_expressions(noise, "", thresh, "A")
mel.connect_material_expressions(threshold, "", thresh, "B")

# soften edge with contrast then dither
contrast = scalar(mat, "Dissolve Contrast", 6.0, -420, 660)
sharp = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -120, 360)
mel.connect_material_expressions(thresh, "", sharp, "A")
mel.connect_material_expressions(contrast, "", sharp, "B")
sat = mel.create_material_expression(mat, unreal.MaterialExpressionSaturate, 40, 360)
mel.connect_material_expressions(sharp, "", sat, "")

dither_class = getattr(unreal, "MaterialExpressionDitherTemporalAA", None)
if dither_class:
    dither = mel.create_material_expression(mat, dither_class, 160, 360)
    mel.connect_material_expressions(sat, "", dither, "Alpha Threshold")
    opacity_src = dither
else:
    opacity_src = sat
mel.connect_material_property(opacity_src, "", unreal.MaterialProperty.MP_OPACITY_MASK)

mel.recompile_material(mat)
EAL.save_loaded_asset(mat)
unreal.log("[JadeBuild] rebuilt M_Burst_JadeDissolve with world-space dissolve (UV-independent)")

# --- reparent instances + colours, Dissolve Amount=1.0 (1=visible, 0=dissolved) ---
variant_settings = [
    ("MI_Burst_Jade_YF", unreal.LinearColor(0.29, 0.38, 0.18, 1.0), unreal.LinearColor(0.42, 0.52, 0.24, 1.0), 0.16),
    ("MI_Burst_Jade_TYS", unreal.LinearColor(0.42, 0.39, 0.22, 1.0), unreal.LinearColor(0.55, 0.49, 0.28, 1.0), 0.21),
    ("MI_Burst_Jade_YZL", unreal.LinearColor(0.25, 0.32, 0.10, 1.0), unreal.LinearColor(0.36, 0.44, 0.15, 1.0), 0.18),
]
for name, color, scatter_color, roughness_value in variant_settings:
    inst = unreal.load_asset(f"{ASSET_DIR}/{name}")
    if not inst:
        continue
    mel.set_material_instance_parent(inst, mat)
    mel.set_material_instance_vector_parameter_value(inst, "Jade Color", color)
    mel.set_material_instance_vector_parameter_value(inst, "Jade Scatter Color", scatter_color)
    mel.set_material_instance_scalar_parameter_value(inst, "Jade Roughness", roughness_value)
    mel.set_material_instance_scalar_parameter_value(inst, "Jade Specular", 0.72)
    mel.set_material_instance_scalar_parameter_value(inst, "Dissolve Amount", 1.0)
    mel.update_material_instance(inst)
    EAL.save_loaded_asset(inst)
    unreal.log(f"[JadeBuild] reparented {name}, Dissolve Amount=1.0")

unreal.log("[JadeBuild] DONE")
