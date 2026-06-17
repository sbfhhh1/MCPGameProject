import unreal


world = unreal.EditorLevelLibrary.get_editor_world()
unreal.log(f"[LevelInspect] World={world.get_path_name() if world else 'None'}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actor_subsystem.get_all_level_actors()
unreal.log(f"[LevelInspect] ActorCount={len(actors)}")

for actor in actors:
    transform = actor.get_actor_transform()
    static_meshes = actor.get_components_by_class(unreal.StaticMeshComponent)
    mesh_paths = []
    for component in static_meshes:
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            mesh_paths.append(mesh.get_path_name())
    unreal.log(
        f"[LevelInspect] Label={actor.get_actor_label()} Name={actor.get_name()} "
        f"Class={actor.get_class().get_name()} "
        f"Location={transform.translation} Rotation={transform.rotation.rotator()} "
        f"Scale={transform.scale3d} Meshes={mesh_paths}"
    )
