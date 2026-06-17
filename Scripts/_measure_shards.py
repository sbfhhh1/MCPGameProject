import unreal
LOG="[MEASURE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    log("NO_PIE")
else:
    target=None
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if "BP_Jade_Shatter" in a.get_name():
            target=a; break
    if target:
        aloc=target.get_actor_location()
        log("actor loc=({:.0f},{:.0f},{:.0f})".format(aloc.x,aloc.y,aloc.z))
        try:
            org,ext=target.get_actor_bounds(False)
            log("ACTOR_BOUNDS origin=({:.0f},{:.0f},{:.0f}) extent=({:.0f},{:.0f},{:.0f})".format(
                org.x,org.y,org.z, ext.x,ext.y,ext.z))
            log("=> jade world box center=({:.0f},{:.0f},{:.0f}) size=({:.0f},{:.0f},{:.0f})".format(
                org.x,org.y,org.z, ext.x*2,ext.y*2,ext.z*2))
        except Exception as e:
            log("bounds err {}".format(e))
        pcm=unreal.GameplayStatics.get_player_camera_manager(world,0)
        if pcm:
            cl=pcm.get_camera_location()
            log("pawn cam=({:.0f},{:.0f},{:.0f}) looks +X, fov 37.5".format(cl.x,cl.y,cl.z))
    else:
        log("no shatter actor")
log("DONE")
