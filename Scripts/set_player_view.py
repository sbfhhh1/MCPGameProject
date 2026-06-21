"""把编辑器视口相机设到玩家机位（PlayerStart 处朝 +X 看向画框）。"""
import unreal

loc = unreal.Vector(-360.0, 0.0, 160.0)
rot = unreal.Rotator()
rot.pitch = 0.0
rot.yaw = 0.0
rot.roll = 0.0
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ues.set_level_viewport_camera_info(loc, rot)
unreal.log("[set_player_view] viewport camera set to player POV")
