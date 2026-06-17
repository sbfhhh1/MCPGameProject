import unreal


LEVEL_PATH = "/Game/ThirdPerson/Lvl_ThirdPerson"
FIXED_CAMERA_TAG = "JoystickFixedCamera"
RECEIVER_TAG = "JoystickSR04Receiver"
CAMERA_LOCK_TAG = "JoystickCameraLock"
NAV_BOUNDS_TAG = "JoystickNavMeshBounds"
CAMERA_LOCATION = unreal.Vector(-1500.0, -1500.0, 1400.0)
CAMERA_ROTATION = unreal.Rotator(0.0, -48.0, 45.0)


def log(message):
    unreal.log(f"[JoystickThirdPersonSetup] {message}")


def get_all_actors():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if subsystem:
        return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def actor_has_tag(actor, tag):
    return any(str(existing_tag) == tag for existing_tag in actor.tags)


def find_actor_by_tag(tag, actor_class=None):
    for actor in get_all_actors():
        if actor_has_tag(actor, tag) and (actor_class is None or isinstance(actor, actor_class)):
            return actor
    return None


def spawn_actor(actor_class, location, rotation):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if subsystem:
        return subsystem.spawn_actor_from_class(actor_class, location, rotation)
    return unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)


def set_tags(actor, *tags):
    existing_tags = [unreal.Name(str(tag)) for tag in actor.tags]
    for tag in tags:
        name = unreal.Name(tag)
        if name not in existing_tags:
            existing_tags.append(name)
    actor.set_editor_property("tags", existing_tags)


def configure_level():
    editor_level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if editor_level:
        editor_level.load_level(LEVEL_PATH)
    else:
        unreal.EditorLevelLibrary.load_level(LEVEL_PATH)

    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("Editor world is not available")

    game_mode_class = unreal.load_class(None, "/Script/MCPGameProject.JoystickSR04ThirdPersonGameMode")
    receiver_class = unreal.load_class(None, "/Script/MCPGameProject.JoystickSR04ReceiverHost")
    camera_lock_class = unreal.load_class(None, "/Script/MCPGameProject.MatrixRuntimeCameraLock")

    if not game_mode_class or not receiver_class or not camera_lock_class:
        raise RuntimeError("Required C++ classes are not loaded. Build the project before running this script.")

    world_settings = world.get_world_settings()
    world_settings.set_editor_property("default_game_mode", game_mode_class)
    log("Set level WorldSettings default_game_mode to JoystickSR04ThirdPersonGameMode")

    camera = find_actor_by_tag(FIXED_CAMERA_TAG, unreal.CameraActor)
    if not camera:
        camera = spawn_actor(
            unreal.CameraActor,
            CAMERA_LOCATION,
            CAMERA_ROTATION,
        )
        camera.set_actor_label("JoystickFixedCamera")
        log("Spawned fixed camera")
    set_tags(camera, FIXED_CAMERA_TAG)
    camera.modify()
    camera.set_actor_location_and_rotation(CAMERA_LOCATION, CAMERA_ROTATION, False, False)

    camera_component = camera.get_component_by_class(unreal.CameraComponent)
    if camera_component:
        camera_component.set_editor_property("field_of_view", 70.0)

    receiver = find_actor_by_tag(RECEIVER_TAG)
    if not receiver:
        receiver = spawn_actor(receiver_class, unreal.Vector(0.0, 0.0, 120.0), unreal.Rotator(0.0, 0.0, 0.0))
        receiver.set_actor_label("JoystickSR04ReceiverHost")
        log("Spawned joystick receiver host")
    receiver.modify()
    set_tags(receiver, RECEIVER_TAG)

    receiver_component = receiver.get_component_by_class(unreal.load_class(None, "/Script/MCPGameProject.JoystickSR04ReceiverComponent"))
    if receiver_component:
        receiver_component.set_editor_property("bDriveMoveTarget", False)
        receiver_component.set_editor_property("bUsePolling", True)
        receiver_component.set_editor_property("UDPPort", 4210)

    lock = find_actor_by_tag(CAMERA_LOCK_TAG)
    if not lock:
        lock = spawn_actor(camera_lock_class, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
        lock.set_actor_label("JoystickFixedCameraLock")
        log("Spawned camera lock")
    lock.modify()
    set_tags(lock, CAMERA_LOCK_TAG)
    lock.set_editor_property("camera_actor", camera)
    lock.set_editor_property("camera_tag", unreal.Name(FIXED_CAMERA_TAG))
    lock.set_editor_property("blend_time", 0.0)
    lock.set_editor_property("bReapplyEveryTick", True)

    nav_bounds = find_actor_by_tag(NAV_BOUNDS_TAG, unreal.NavMeshBoundsVolume)
    if not nav_bounds:
        nav_bounds = spawn_actor(
            unreal.NavMeshBoundsVolume,
            unreal.Vector(0.0, 0.0, 250.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        nav_bounds.set_actor_label("JoystickNavMeshBounds")
        log("Spawned NavMeshBoundsVolume")
    nav_bounds.modify()
    set_tags(nav_bounds, NAV_BOUNDS_TAG)
    nav_bounds.set_actor_location_and_rotation(unreal.Vector(0.0, 0.0, 250.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)
    nav_bounds.set_actor_scale3d(unreal.Vector(45.0, 45.0, 5.0))

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, LEVEL_PATH):
        raise RuntimeError(f"Failed to save map {LEVEL_PATH}")
    log(f"Saved map {LEVEL_PATH}")


configure_level()
