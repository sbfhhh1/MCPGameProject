import unreal
LOG="[SETXF]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

BP_PATH = "/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade"
bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)

# 每个组件的目标相对 transform（A=ec021d65, B=f8ed59ab, C=a1276204）
def rot(roll,pitch,yaw):
    r = unreal.Rotator(); r.roll=roll; r.pitch=pitch; r.yaw=yaw; return r
SPEC = {
    "Static Mesh A": (unreal.Vector(0,0,0),   rot(90,0,0),   200.0),
    "Static Mesh B": (unreal.Vector(0,0,20),  rot(90,0,180), 200.0),
    "Static Mesh C": (unreal.Vector(0,0,0),   rot(90,0,0),   200.0),
}

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
log("gathered {} subobjects".format(len(handles)))
changed=0
for h in handles:
    data = sds.k2_find_subobject_data_from_handle(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    if obj is None: continue
    nm = obj.get_name()
    cls = obj.get_class().get_name()
    if cls != "StaticMeshComponent": continue
    for key,(loc,r,s) in SPEC.items():
        if key.replace(" ","") in nm.replace(" ",""):
            obj.set_editor_property("relative_location", loc)
            obj.set_editor_property("relative_rotation", r)
            obj.set_editor_property("relative_scale3d", unreal.Vector(s,s,s))
            nl=obj.get_editor_property("relative_location"); nr=obj.get_editor_property("relative_rotation"); ns=obj.get_editor_property("relative_scale3d")
            log("  '{}' -> loc({:.0f},{:.0f},{:.0f}) rot(r{:.0f},p{:.0f},y{:.0f}) scale{:.0f}".format(
                nm, nl.x,nl.y,nl.z, nr.roll,nr.pitch,nr.yaw, ns.x))
            changed+=1
            break
log("changed {} comps".format(changed))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(BP_PATH)
log("compiled+saved DONE")
