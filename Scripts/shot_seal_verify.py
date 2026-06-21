# -*- coding: utf-8 -*-
"""贴近看程序网格印章顶面的字与法线。"""
import unreal

loc = unreal.Vector(300.0, -45.0, 110.0)
rot = unreal.Rotator()
rot.pitch = -28.0
rot.yaw = 48.0
rot.roll = 0.0
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(loc, rot)
unreal.AutomationLibrary.take_high_res_screenshot(1400, 1050, "SealFix_verify.png")
unreal.log("[shot] requested")
