import unreal


MAP_PATH = "/Game/TobiiEyeTracker5/Examples/ScreenBasedPrefabDemo"


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError(f"Could not load {MAP_PATH}")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
demos = [actor for actor in actors if actor.get_class().get_name() == "TobiiScreenBasedDemoActor"]
if len(demos) != 1:
    raise RuntimeError(f"Expected one TobiiScreenBasedDemoActor, found {len(demos)}")

targets = list(demos[0].get_editor_property("gaze_targets"))
target_labels = [target.get_actor_label() for target in targets if target]
expected = ["CubeLeft", "CubeMiddle", "CubeRight"]
if target_labels and target_labels != expected:
    raise RuntimeError(f"Unexpected gaze targets: {target_labels}")
if not target_labels:
    unreal.log_warning("Gaze target references are empty; runtime name/label recovery will be used.")

required_labels = {
    "Tobii_FixedCamera",
    "Tobii_CameraLock",
    "Tobii_ScreenBasedPrefabDemo",
    "Sphere",
    "Capsule",
}
labels = {actor.get_actor_label() for actor in actors}
missing = sorted(required_labels - labels)
if missing:
    raise RuntimeError(f"Missing required actors: {missing}")

unreal.log(f"Tobii demo verification passed. Targets: {target_labels}")
