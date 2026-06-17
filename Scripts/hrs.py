import unreal
w=unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720')
unreal.log('[HRS] issued')