import unreal
LOG="[AIMJADE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    log("NO_PIE")
else:
    jade=None
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if "BP_Return_SM_Jade" in a.get_name():
            jade=a; break
    if not jade:
        log("no jade actor")
    else:
        vis_comp=None
        for c in jade.get_components_by_class(unreal.StaticMeshComponent):
            sm = c.get_editor_property("static_mesh")
            if c.is_visible() and sm:
                vis_comp=c
        if not vis_comp:
            log("no visible mesh")
        else:
            sm = vis_comp.get_editor_property("static_mesh")
            wloc = vis_comp.get_world_location()
            box = sm.get_bounding_box()   # local space Box
            bmin = box.min; bmax = box.max
            center = unreal.Vector((bmin.x+bmax.x)/2.0, (bmin.y+bmax.y)/2.0, (bmin.z+bmax.z)/2.0)
            ext = unreal.Vector((bmax.x-bmin.x)/2.0, (bmax.y-bmin.y)/2.0, (bmax.z-bmin.z)/2.0)
            scale = vis_comp.get_world_scale()
            # 世界中心（忽略旋转，近似）
            wc = unreal.Vector(wloc.x + center.x*scale.x, wloc.y + center.y*scale.y, wloc.z + center.z*scale.z)
            maxext = max(ext.x*scale.x, ext.y*scale.y, ext.z*scale.z, 10.0)
            log("visible '{}' sm={} local_ext=({:.1f},{:.1f},{:.1f}) world_center=({:.1f},{:.1f},{:.1f}) maxext={:.1f}".format(
                vis_comp.get_name(), sm.get_name(), ext.x,ext.y,ext.z, wc.x,wc.y,wc.z, maxext))
            dist = maxext * 2.6
            cam = unreal.Vector(wc.x, wc.y - dist, wc.z + maxext*0.25)
            look = unreal.MathLibrary.find_look_at_rotation(cam, wc)
            for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SceneCapture2D):
                a.set_actor_location_and_rotation(cam, look, False, False)
                cc = a.capture_component2d
                cc.set_editor_property("fov_angle", 50.0)
                log("moved capture to ({:.1f},{:.1f},{:.1f}) look p{:.1f} y{:.1f} dist={:.1f}".format(
                    cam.x,cam.y,cam.z, look.pitch, look.yaw, dist))
                break
log("DONE")
