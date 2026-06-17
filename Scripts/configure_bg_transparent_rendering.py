import unreal


for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if actor.get_actor_label().lower() != "bg":
        continue

    actor.modify()
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        component.modify()
        component.set_editor_property("cast_shadow", False)
        component.set_editor_property("cast_dynamic_shadow", False)
        component.set_editor_property("cast_static_shadow", False)
        component.set_editor_property("affect_distance_field_lighting", False)
        component.set_editor_property("visible_in_ray_tracing", False)
        unreal.log(f"[BGTransparent] Disabled shadow and ray tracing visibility on {component.get_name()}")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
