import unreal


ASSET_DIR = "/Game/TransformationVFX/SM2SM"
MATERIAL_NAME = "M_Burst_ParticleFade"


def scalar(material, name, default, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", default)
    return expression


path = f"{ASSET_DIR}/{MATERIAL_NAME}"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)

tools = unreal.AssetToolsHelpers.get_asset_tools()
material = tools.create_asset(MATERIAL_NAME, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())
material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
material.set_editor_property("two_sided", True)

mel = unreal.MaterialEditingLibrary
particle_color = mel.create_material_expression(material, unreal.MaterialExpressionParticleColor, -700, -100)
brightness = scalar(material, "Brightness", 8.0, -700, 100)
fade_opacity = scalar(material, "Fade Opacity", 1.0, -700, 220)

emissive = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -350, -80)
opacity = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -350, 180)
mel.connect_material_expressions(particle_color, "", emissive, "A")
mel.connect_material_expressions(brightness, "", emissive, "B")
mel.connect_material_expressions(particle_color, "A", opacity, "A")
mel.connect_material_expressions(fade_opacity, "", opacity, "B")

mel.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material)
unreal.log(f"[BurstFadeMaterial] Created {path}")

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        component.modify()
        component.set_editor_property("particle_material", material)
        component.set_editor_property("state_particle_materials", [material, material, material])
        component.set_editor_property("particle_fade_out_duration", 1.5)
        component.set_editor_property("particle_fade_out_ease_exponent", 2.0)
        unreal.log(f"[BurstFadeMaterial] Assigned to {actor.get_actor_label()}")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
