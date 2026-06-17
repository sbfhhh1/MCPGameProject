import unreal


subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for name in dir(subsystem):
    if "play" in name.lower() or "simulate" in name.lower():
        unreal.log(f"[PlayAPI] {name}")
