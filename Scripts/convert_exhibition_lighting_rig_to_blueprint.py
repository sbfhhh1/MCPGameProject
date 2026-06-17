import unreal


ASSET_DIR = "/Game/TransformationVFX/SM2SM"
BLUEPRINT_NAME = "BP_ExhibitionLightingRig_Professional"
BLUEPRINT_PATH = f"{ASSET_DIR}/{BLUEPRINT_NAME}"
ACTOR_LABEL = "ExhibitionLightingRig_Professional"

COPY_PROPERTIES = [
    "key_intensity",
    "fill_intensity",
    "top_intensity",
    "rim_intensity",
    "warm_temperature",
    "cool_temperature",
    "exposure_min_ev100",
    "exposure_max_ev100",
    "exposure_compensation",
    "bloom_intensity",
    "vignette_intensity",
    "ambient_occlusion_intensity",
]


actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actor_subsystem.get_all_level_actors()
source_actor = next(
    (actor for actor in actors if actor.get_actor_label() == ACTOR_LABEL),
    None,
)
if not source_actor:
    raise RuntimeError(f"Actor not found: {ACTOR_LABEL}")

source_transform = source_actor.get_actor_transform()
source_folder = source_actor.get_folder_path()
source_values = {
    name: source_actor.get_editor_property(name)
    for name in COPY_PROPERTIES
}

if unreal.EditorAssetLibrary.does_asset_exist(BLUEPRINT_PATH):
    blueprint = unreal.load_asset(BLUEPRINT_PATH)
else:
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.ExhibitionLightingRig)
    blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        BLUEPRINT_NAME,
        ASSET_DIR,
        unreal.Blueprint,
        factory,
    )

if not blueprint:
    raise RuntimeError(f"Failed to create blueprint: {BLUEPRINT_PATH}")

unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
generated_class = blueprint.generated_class()
cdo = unreal.get_default_object(generated_class)
for name, value in source_values.items():
    cdo.set_editor_property(name, value)
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
unreal.EditorAssetLibrary.save_loaded_asset(blueprint)

new_actor = actor_subsystem.spawn_actor_from_class(
    generated_class,
    source_transform.translation,
    source_transform.rotation.rotator(),
)
if not new_actor:
    raise RuntimeError("Failed to spawn blueprint lighting rig")

new_actor.set_actor_transform(source_transform, False, True)
new_actor.set_actor_label(ACTOR_LABEL)
new_actor.set_folder_path(source_folder)
for name, value in source_values.items():
    new_actor.set_editor_property(name, value)

actor_subsystem.destroy_actor(source_actor)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log(
    f"[LightingRigBlueprint] Replaced {ACTOR_LABEL} with {BLUEPRINT_PATH} "
    f"at {source_transform.translation}"
)
