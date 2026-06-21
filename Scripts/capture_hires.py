"""设玩家机位并用 HighResShot 强制重渲染截图（绕开视口非实时不刷新问题）。"""
import unreal

loc = unreal.Vector(-300.0, 0.0, 165.0)
rot = unreal.Rotator(); rot.pitch = 0.0; rot.yaw = 0.0; rot.roll = 0.0
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(loc, rot)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "HighResShot 1200x900")
unreal.log("[capture_hires] HighResShot issued")
