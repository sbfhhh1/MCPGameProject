import unreal


BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
BURST_LABEL = "BP_Burst_SM_Test"
SOURCE_LABELS = ["YF", "TYS", "YZL"]
COMPONENT_VARIABLES = ["Static Mesh A", "Static Mesh B", "Static Mesh C"]
VARIANT_PATHS = [
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YF",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_TYS",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YZL",
]

bp = unreal.load_asset(BP_PATH)
variants = [unreal.load_asset(path) for path in VARIANT_PATHS]
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
source_actors = {actor.get_actor_label(): actor for actor in actors if actor.get_actor_label() in SOURCE_LABELS}
burst_actor = next((actor for actor in actors if actor.get_actor_label() == BURST_LABEL), None)

meshes = []
for label in SOURCE_LABELS:
    component = source_actors[label].get_components_by_class(unreal.StaticMeshComponent)[0]
    meshes.append(component.get_editor_property("static_mesh"))

subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
library = unreal.SubobjectDataBlueprintFunctionLibrary
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)

template_by_variable = {}
for handle in handles:
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    variable_name = str(library.get_variable_name(data))
    obj = library.get_object_for_blueprint(data, bp)
    if obj:
        template_by_variable[variable_name] = obj

for index, variable_name in enumerate(COMPONENT_VARIABLES):
    component = template_by_variable.get(variable_name)
    if not component:
        raise RuntimeError(f"Missing Blueprint subobject {variable_name}")
    component.modify()
    component.set_editor_property("static_mesh", meshes[index])
    component.set_material(0, variants[index])
    unreal.log(
        f"[BurstJadeSubobject] {variable_name} Mesh={meshes[index].get_path_name()} "
        f"Material={variants[index].get_path_name()}")

switcher = template_by_variable.get("NumberKeyBurstStateSwitcher")
if not switcher:
    raise RuntimeError("Missing NumberKeyBurstStateSwitcher Blueprint subobject")

switcher.modify()
switcher.set_editor_property("state_fade_materials", variants)
switcher.set_editor_property("fallback_model_fade_material", variants[0])
switcher.set_editor_property("model_fade_start_dissolve", 0.0)
switcher.set_editor_property("model_fade_end_dissolve", 0.65)
switcher.set_editor_property("model_fade_in_duration", 2.0)
switcher.set_editor_property("particle_fade_out_duration", 2.0)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)

if burst_actor:
    state_components = {}
    for component in burst_actor.get_components_by_class(unreal.StaticMeshComponent):
        normalized = component.get_name().replace(" ", "").replace("_", "")
        for expected in ["StaticMeshA", "StaticMeshB", "StaticMeshC"]:
            if expected in normalized:
                state_components[expected] = component

    for index, expected in enumerate(["StaticMeshA", "StaticMeshB", "StaticMeshC"]):
        component = state_components[expected]
        source_actor = source_actors[SOURCE_LABELS[index]]
        component.modify()
        component.set_world_location(
            unreal.Vector(
                burst_actor.get_actor_location().x,
                burst_actor.get_actor_location().y,
                170.0),
            False,
            True)
        component.set_world_rotation(source_actor.get_actor_rotation(), False, True)
        component.set_world_scale3d(source_actor.get_actor_scale3d())
        for slot in range(max(component.get_num_materials(), 1)):
            component.set_material(slot, variants[index])
        component.set_visibility(index == 0, True)

    for runtime_switcher in burst_actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        runtime_switcher.set_editor_property("state_fade_materials", variants)
        runtime_switcher.set_editor_property("fallback_model_fade_material", variants[0])

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[BurstJadeSubobject] Blueprint templates and BP_Burst_SM_Test configured")
