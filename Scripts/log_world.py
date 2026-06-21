# -*- coding: utf-8 -*-
import unreal
w = unreal.EditorLevelLibrary.get_editor_world()
name = w.get_name() if w else "NONE"
path = w.get_path_name() if w else "NONE"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
c = len(sub.get_all_level_actors())
unreal.log("[WORLD_CHECK] world=%s path=%s actors=%d" % (name, path, c))
