import unreal


SYSTEM_PATH = "/Game/TransformationVFX/Niagara/NS_Inhalation_SM"
MATERIAL_PATH = "/Game/TransformationVFX/Material/CharactorMaterial/MI_Manny_Particle"

system = unreal.load_asset(SYSTEM_PATH)
material = unreal.load_asset(MATERIAL_PATH)
if not system:
    raise RuntimeError(f"Missing Niagara system: {SYSTEM_PATH}")
if not material:
    raise RuntimeError(f"Missing particle material: {MATERIAL_PATH}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actor_subsystem.get_all_level_actors():
    switchers = actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent)
    if not switchers:
        continue

    switcher = switchers[0]
    switcher.modify()
    switcher.set_editor_property("particle_system", system)
    switcher.set_editor_property("particle_current_mode", 0)
    switcher.set_editor_property("initial_transformation_alpha", 0.0)
    switcher.set_editor_property("first_half_end_transformation_alpha", 0.5)
    switcher.set_editor_property("particle_material", material)
    switcher.set_editor_property("state_particle_materials", [material, material, material])

    for niagara in actor.get_components_by_class(unreal.NiagaraComponent):
        niagara.modify()
        niagara.set_asset(system)
        niagara.set_variable_int("User.CurrentMode", 0)
        niagara.set_variable_float("User.Transformation Alpha", 0.0)
        niagara.set_variable_float("User.TransformationAlpha", 0.0)
        niagara.set_variable_float("User.Morph Alpha", 0.0)
        niagara.deactivate()
        niagara.set_visibility(False, True)

    unreal.log(
        f"[BurstForceRestore] Actor={actor.get_actor_label()} "
        f"System={SYSTEM_PATH} Mode=0 Material={MATERIAL_PATH}"
    )

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
