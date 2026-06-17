import unreal


BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
BURST_LABEL = "BP_Burst_SM_Test"
SOURCE_LABELS = ["YF", "TYS", "YZL"]
COMPONENT_NAMES = ["StaticMeshA", "StaticMeshB", "StaticMeshC"]
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

mesh_by_label = {}
scale_by_label = {}
rotation_by_label = {}
for label in SOURCE_LABELS:
    actor = source_actors[label]
    mesh_by_label[label] = actor.get_components_by_class(unreal.StaticMeshComponent)[0].get_editor_property("static_mesh")
    scale_by_label[label] = actor.get_actor_scale3d()
    rotation_by_label[label] = actor.get_actor_rotation()

templates = unreal.BlueprintEditorLibrary.get_blueprint_components(bp)
state_templates = {}
switcher_template = None
for template in templates:
    normalized = template.get_name().replace(" ", "").replace("_", "").replace("GENVARIABLE", "")
    for expected in COMPONENT_NAMES:
        if expected in normalized and isinstance(template, unreal.StaticMeshComponent):
            state_templates[expected] = template
    if isinstance(template, unreal.BurstMeshStateSwitcherComponent):
        switcher_template = template

for index, (label, component_name) in enumerate(zip(SOURCE_LABELS, COMPONENT_NAMES)):
    component = state_templates.get(component_name)
    if not component:
        raise RuntimeError(f"Blueprint template missing {component_name}")
    component.modify()
    component.set_editor_property("static_mesh", mesh_by_label[label])
    component.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 80.0))
    component.set_editor_property("relative_rotation", rotation_by_label[label])
    component.set_editor_property("relative_scale3d", scale_by_label[label])
    component.set_material(0, variants[index])
    unreal.log(
        f"[BurstJadeTemplate] {component_name}={mesh_by_label[label].get_path_name()} "
        f"Material={variants[index].get_path_name()}")

if switcher_template:
    switcher_template.modify()
    switcher_template.set_editor_property("state_fade_materials", variants)
    switcher_template.set_editor_property("fallback_model_fade_material", variants[0])
    switcher_template.set_editor_property("model_fade_start_dissolve", 0.0)
    switcher_template.set_editor_property("model_fade_end_dissolve", 0.65)
    switcher_template.set_editor_property("model_fade_in_duration", 2.0)
    switcher_template.set_editor_property("particle_fade_out_duration", 2.0)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)

if burst_actor:
    burst_actor.rerun_construction_scripts()
    for switcher in burst_actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        switcher.set_editor_property("state_fade_materials", variants)
        switcher.set_editor_property("fallback_model_fade_material", variants[0])

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[BurstJadeTemplate] Blueprint templates configured and current actor reconstructed")
