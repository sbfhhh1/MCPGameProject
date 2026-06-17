import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

ASSET_DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
SRC = "/Game/TransformationVFX/Material/ObjectMaterial/M_Chair_Dissolve"
NEW = f"{ASSET_DIR}/M_Burst_JadeDissolve"


def scalar(material, name, default, x, y):
    e = mel.create_material_expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", default)
    return e


def vector(material, name, value, x, y):
    e = mel.create_material_expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", value)
    return e


# --- 1. duplicate chair dissolve (keeps original noise-driven dissolve mask) ---
freshly_created = False
if not EAL.does_asset_exist(NEW):
    dup = EAL.duplicate_asset(SRC, NEW)
    if not dup:
        raise RuntimeError("duplicate failed")
    freshly_created = True
    unreal.log(f"[JadeDissolve] duplicated {SRC} -> {NEW}")

mat = unreal.load_asset(NEW)

# --- 2. override appearance to jade SSS, leave OpacityMask (dissolve) untouched ---
if freshly_created:
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
    mat.set_editor_property("two_sided", False)

    jade_color = vector(mat, "Jade Color", unreal.LinearColor(0.25, 0.32, 0.10, 1.0), -1500, -500)
    mel.connect_material_property(jade_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    scatter = vector(mat, "Jade Scatter Color", unreal.LinearColor(0.34, 0.42, 0.15, 1.0), -1500, -360)
    mel.connect_material_property(scatter, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)

    rough = scalar(mat, "Jade Roughness", 0.18, -1500, -220)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    spec = scalar(mat, "Jade Specular", 0.65, -1500, -120)
    mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

    metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -1500, -20)
    metal.set_editor_property("r", 0.0)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)

    mel.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    unreal.log("[JadeDissolve] reworked appearance: BaseColor/SSS/Roughness/Specular/Metallic; dissolve mask preserved")

# --- 3. reparent the three jade instances + keep their colour variance ---
variant_settings = [
    ("MI_Burst_Jade_YF", unreal.LinearColor(0.29, 0.38, 0.18, 1.0), unreal.LinearColor(0.42, 0.52, 0.24, 1.0), 0.16),
    ("MI_Burst_Jade_TYS", unreal.LinearColor(0.42, 0.39, 0.22, 1.0), unreal.LinearColor(0.55, 0.49, 0.28, 1.0), 0.21),
    ("MI_Burst_Jade_YZL", unreal.LinearColor(0.25, 0.32, 0.10, 1.0), unreal.LinearColor(0.36, 0.44, 0.15, 1.0), 0.18),
]

for name, color, scatter_color, roughness_value in variant_settings:
    path = f"{ASSET_DIR}/{name}"
    inst = unreal.load_asset(path)
    if not inst:
        unreal.log_warning(f"[JadeDissolve] missing instance {path}")
        continue
    mel.set_material_instance_parent(inst, mat)
    mel.set_material_instance_vector_parameter_value(inst, "Jade Color", color)
    mel.set_material_instance_vector_parameter_value(inst, "Jade Scatter Color", scatter_color)
    mel.set_material_instance_scalar_parameter_value(inst, "Jade Roughness", roughness_value)
    mel.set_material_instance_scalar_parameter_value(inst, "Jade Specular", 0.72)
    # chair-dissolve semantics: 1.0 = fully visible, 0.0 = fully dissolved away
    # initial state shows full model; fade-in driven 0.0 -> 1.0 at runtime
    mel.set_material_instance_scalar_parameter_value(inst, "Dissolve Amount", 1.0)
    mel.update_material_instance(inst)
    EAL.save_loaded_asset(inst)
    unreal.log(f"[JadeDissolve] reparented {name} -> M_Burst_JadeDissolve, Dissolve Amount=0.0")

unreal.log("[JadeDissolve] DONE")
