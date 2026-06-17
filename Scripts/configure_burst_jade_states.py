import unreal


ASSET_DIR = "/Game/TransformationVFX/SM2SM/jude/BurstJade"
PARENT_NAME = "M_Burst_JadeFade"
BURST_LABEL = "BP_Burst_SM_Test"
SOURCE_LABELS = ["YF", "TYS", "YZL"]
COMPONENT_NAMES = ["StaticMeshA", "StaticMeshB", "StaticMeshC"]


def scalar(material, name, default, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", default)
    return expression


def vector(material, name, value, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", value)
    return expression


unreal.EditorAssetLibrary.make_directory(ASSET_DIR)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

parent_path = f"{ASSET_DIR}/{PARENT_NAME}"
if unreal.EditorAssetLibrary.does_asset_exist(parent_path):
    parent = unreal.load_asset(parent_path)
    mel.delete_all_material_expressions(parent)
else:
    parent = tools.create_asset(PARENT_NAME, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())

parent.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
parent.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
parent.set_editor_property("two_sided", False)
parent.set_editor_property("opacity_mask_clip_value", 0.05)

base_color = vector(parent, "Jade Color", unreal.LinearColor(0.25, 0.32, 0.10, 1.0), -700, -240)
scatter_color = vector(parent, "Jade Scatter Color", unreal.LinearColor(0.34, 0.42, 0.15, 1.0), -700, -120)
roughness = scalar(parent, "Jade Roughness", 0.18, -700, 0)
specular = scalar(parent, "Jade Specular", 0.65, -700, 100)
dissolve = scalar(parent, "Dissolve Amount", 1.0, -700, 220)

divide = mel.create_material_expression(parent, unreal.MaterialExpressionDivide, -430, 220)
fade_end = mel.create_material_expression(parent, unreal.MaterialExpressionConstant, -700, 310)
fade_end.set_editor_property("r", 0.65)
mel.connect_material_expressions(dissolve, "", divide, "A")
mel.connect_material_expressions(fade_end, "", divide, "B")

saturate = mel.create_material_expression(parent, unreal.MaterialExpressionSaturate, -220, 220)
mel.connect_material_expressions(divide, "", saturate, "")

dither_class = getattr(unreal, "MaterialExpressionDitherTemporalAA", None)
if dither_class:
    dither = mel.create_material_expression(parent, dither_class, 0, 220)
    mel.connect_material_expressions(saturate, "", dither, "Alpha Threshold")
    opacity_source = dither
else:
    opacity_source = saturate

mel.connect_material_property(base_color, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(scatter_color, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
mel.connect_material_property(opacity_source, "", unreal.MaterialProperty.MP_OPACITY_MASK)
mel.recompile_material(parent)
unreal.EditorAssetLibrary.save_loaded_asset(parent)

variant_settings = [
    ("MI_Burst_Jade_YF", unreal.LinearColor(0.29, 0.38, 0.18, 1.0), unreal.LinearColor(0.42, 0.52, 0.24, 1.0), 0.16),
    ("MI_Burst_Jade_TYS", unreal.LinearColor(0.42, 0.39, 0.22, 1.0), unreal.LinearColor(0.55, 0.49, 0.28, 1.0), 0.21),
    ("MI_Burst_Jade_YZL", unreal.LinearColor(0.25, 0.32, 0.10, 1.0), unreal.LinearColor(0.36, 0.44, 0.15, 1.0), 0.18),
]

variants = []
for name, color, scatter, roughness_value in variant_settings:
    path = f"{ASSET_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        instance = unreal.load_asset(path)
    else:
        instance = tools.create_asset(
            name, ASSET_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(instance, parent)
    mel.set_material_instance_vector_parameter_value(instance, "Jade Color", color)
    mel.set_material_instance_vector_parameter_value(instance, "Jade Scatter Color", scatter)
    mel.set_material_instance_scalar_parameter_value(instance, "Jade Roughness", roughness_value)
    mel.set_material_instance_scalar_parameter_value(instance, "Jade Specular", 0.72)
    mel.set_material_instance_scalar_parameter_value(instance, "Dissolve Amount", 1.0)
    mel.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    variants.append(instance)

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
source_actors = {actor.get_actor_label(): actor for actor in actors if actor.get_actor_label() in SOURCE_LABELS}
burst_actor = next((actor for actor in actors if actor.get_actor_label() == BURST_LABEL), None)
if not burst_actor:
    raise RuntimeError(f"Could not find {BURST_LABEL}")

state_components = {}
for component in burst_actor.get_components_by_class(unreal.StaticMeshComponent):
    normalized = component.get_name().replace(" ", "").replace("_", "")
    for expected in COMPONENT_NAMES:
        if expected in normalized:
            state_components[expected] = component

for index, (source_label, component_name) in enumerate(zip(SOURCE_LABELS, COMPONENT_NAMES)):
    source_actor = source_actors.get(source_label)
    component = state_components.get(component_name)
    if not source_actor or not component:
        raise RuntimeError(f"Missing source actor or component for {source_label}/{component_name}")

    source_component = source_actor.get_components_by_class(unreal.StaticMeshComponent)[0]
    mesh = source_component.get_editor_property("static_mesh")
    component.modify()
    component.set_editor_property("static_mesh", mesh)
    component.set_world_location(
        unreal.Vector(burst_actor.get_actor_location().x, burst_actor.get_actor_location().y, 170.0),
        False, True)
    component.set_world_rotation(source_actor.get_actor_rotation(), False, True)
    component.set_world_scale3d(source_actor.get_actor_scale3d())
    for slot in range(max(component.get_num_materials(), 1)):
        component.set_material(slot, variants[index])
    component.set_visibility(index == 0, True)
    unreal.log(
        f"[BurstJadeConfig] State={index + 1} Source={source_label} "
        f"Mesh={mesh.get_path_name()} Material={variants[index].get_path_name()}")

for switcher in burst_actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
    switcher.modify()
    switcher.set_editor_property("state_fade_materials", variants)
    switcher.set_editor_property("fallback_model_fade_material", variants[0])
    switcher.set_editor_property("model_fade_start_dissolve", 0.0)
    switcher.set_editor_property("model_fade_end_dissolve", 0.65)
    switcher.set_editor_property("model_fade_in_duration", 2.0)
    switcher.set_editor_property("particle_fade_out_duration", 2.0)

for source_actor in source_actors.values():
    source_actor.set_actor_hidden_in_game(True)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[BurstJadeConfig] Configured BP_Burst_SM_Test with YF/TYS/YZL jade states")
