import unreal


TARGET_LABEL = "YZL"
INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"
instance = unreal.load_asset(INSTANCE_PATH)

for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label().lower() != TARGET_LABEL.lower():
        continue
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if not mesh:
            continue

        settings = mesh.get_editor_property("nanite_settings")
        settings.enabled = False
        mesh.set_editor_property("nanite_settings", settings)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)

        component.set_editor_property("static_mesh", None)
        component.set_editor_property("static_mesh", mesh)
        for slot in range(max(component.get_num_materials(), 1)):
            component.set_material(slot, instance)
        unreal.log(f"[JadeNanite] Disabled Nanite and refreshed {mesh.get_path_name()}")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
