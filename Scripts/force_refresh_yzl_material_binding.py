import unreal


TARGET_LABEL = "YZL"
INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"

instance = unreal.load_asset(INSTANCE_PATH)
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label().lower() != TARGET_LABEL.lower():
        continue
    actor.modify()
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        component.modify()
        slot_count = max(component.get_num_materials(), 1)
        for slot in range(slot_count):
            component.set_material(slot, None)
        for slot in range(slot_count):
            component.set_material(slot, instance)
        component.set_visibility(False, True)
        component.set_visibility(True, True)
        unreal.log(f"[JadeBinding] Force-refreshed {actor.get_actor_label()} material slots")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
