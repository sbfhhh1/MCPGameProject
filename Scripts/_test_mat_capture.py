import unreal
LOG="[TESTMAT]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

MAT_PATH = getattr(unreal, "_test_mat", "/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
OUT = getattr(unreal, "_test_out", "mat_jadedissolve.png")
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)

world = unreal.EditorLevelLibrary.get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 找 BP_Return_SM_Jade，给可见网格(及全部)设测试材质
jade=None; cap=None
for a in eas.get_all_level_actors():
    if "BP_Return_SM_Jade" in a.get_class().get_name():
        jade=a
    if a.get_actor_label()=="DiagCapture":
        cap=a
if not jade:
    log("no jade");
else:
    for c in jade.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_num_materials()
        for i in range(max(n,1)):
            mid = c.create_dynamic_material_instance(i, mat)
            if mid:
                try: mid.set_scalar_parameter_value("Dissolve Amount", 1.0)
                except Exception: pass
    log("applied {} (Dissolve=1) to jade meshes".format(MAT_PATH.split('/')[-1]))

# 相机到 pawn 机位
if cap is None:
    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(-420,0,160), unreal.Rotator(0,0,0))
    cap.set_actor_label("DiagCapture")
    rt = unreal.RenderingLibrary.create_render_target2d(world, 900,600, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    cap.capture_component2d.set_editor_property("texture_target", rt)
    cap.capture_component2d.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_actor_location_and_rotation(unreal.Vector(-420,0,160), unreal.Rotator(0,0,0), False, False)
cc = cap.capture_component2d
cc.set_editor_property("fov_angle", 37.5)
rt = cc.get_editor_property("texture_target")
cc.capture_scene()
unreal.RenderingLibrary.export_render_target(world, rt, "C:/UE_Project/MCPGameProject/Saved/_capframes", OUT)
log("exported {}".format(OUT))
log("DONE")
