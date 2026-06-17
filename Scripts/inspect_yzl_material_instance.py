import unreal


INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"
TARGET_LABEL = "YZL"

instance = unreal.load_asset(INSTANCE_PATH)
unreal.log(f"[JadeInspect] instance={instance.get_path_name() if instance else 'None'}")

if instance:
    parent = instance.get_editor_property("parent")
    unreal.log(f"[JadeInspect] parent={parent.get_path_name() if parent else 'None'}")

    scalar_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(instance)
    vector_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(instance)
    unreal.log(f"[JadeInspect] scalar_names={[str(name) for name in scalar_names]}")
    unreal.log(f"[JadeInspect] vector_names={[str(name) for name in vector_names]}")

    for name in scalar_names:
        value = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(instance, name)
        unreal.log(f"[JadeInspect] scalar {name}={value}")

    for name in vector_names:
        value = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(instance, name)
        unreal.log(f"[JadeInspect] vector {name}={value}")

for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label().lower() != TARGET_LABEL.lower():
        continue
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        for slot in range(component.get_num_materials()):
            material = component.get_material(slot)
            unreal.log(
                f"[JadeInspect] actor={actor.get_actor_label()} slot={slot} "
                f"material={material.get_path_name() if material else 'None'}")
