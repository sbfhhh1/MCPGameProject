# -*- coding: utf-8 -*-
import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/TransformationVFX/SM2SM/SM2SM")
w = unreal.EditorLevelLibrary.get_editor_world()
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.log("[load_sm2sm] world=%s actors=%d" % (w.get_name() if w else "NONE", len(sub.get_all_level_actors())))
