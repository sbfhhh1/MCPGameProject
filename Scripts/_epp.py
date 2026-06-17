import unreal
try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
except Exception: pass
