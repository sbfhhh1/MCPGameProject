import unreal
LOG="[JWORLD]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
GUIDS=["20260613130638_a1276204","20260613132029_aabaf03a","20260613133607_ec021d65","20260613123723_f8ed59ab"]

world = unreal.EditorLevelLibrary.get_game_world()
src = "PIE" if world else "EDITOR"
if not world:
    world = unreal.EditorLevelLibrary.get_editor_world()
log("world_src={} {}".format(src, world.get_path_name()))

# pawn 相机 POV
try:
    pcm = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    if pcm:
        cl=pcm.get_camera_location(); cr=pcm.get_camera_rotation()
        log("PAWN_CAM loc=({:.1f},{:.1f},{:.1f}) rot=(p{:.1f},y{:.1f},r{:.1f}) fov={:.1f}".format(
            cl.x,cl.y,cl.z, cr.pitch,cr.yaw,cr.roll, pcm.get_fov_angle()))
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    if pawn:
        pl=pawn.get_actor_location()
        log("PAWN loc=({:.1f},{:.1f},{:.1f}) class={}".format(pl.x,pl.y,pl.z, pawn.get_class().get_name()))
except Exception as e:
    log("cam err {}".format(e))

# 所有用玉石网格的 actor
for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.get_editor_property("static_mesh")
        if sm and any(g in sm.get_name() for g in GUIDS):
            ws=c.get_world_scale(); wl=c.get_world_location(); vis=c.is_visible()
            box=sm.get_bounding_box()
            sx=(box.max.x-box.min.x)*ws.x; sy=(box.max.y-box.min.y)*ws.y; sz=(box.max.z-box.min.z)*ws.z
            log("  '{}' comp='{}' vis={} wloc=({:.0f},{:.0f},{:.0f}) wscale=({:.1f},{:.1f},{:.1f}) worldsize=({:.1f},{:.1f},{:.1f}) mesh={}".format(
                a.get_name(), c.get_name(), vis, wl.x,wl.y,wl.z, ws.x,ws.y,ws.z, sx,sy,sz, sm.get_name()))
log("DONE")
