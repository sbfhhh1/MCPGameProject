import unreal
LOG="[SHATTERBP]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

PKG="/Game/TransformationVFX/SM2SM"
NAME="BP_Jade_Shatter"
full=PKG+"/"+NAME

if unreal.EditorAssetLibrary.does_asset_exist(full):
    unreal.EditorAssetLibrary.delete_asset(full)

# 创建 Actor 蓝图
factory=unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.Actor)
tools=unreal.AssetToolsHelpers.get_asset_tools()
bp=tools.create_asset(NAME, PKG, unreal.Blueprint, factory)
log("created bp={}".format(bp.get_name() if bp else "None"))

# 挂载碎块组件
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles=sds.k2_gather_subobject_data_for_blueprint(bp)
log("root handles={}".format(len(handles)))
root_handle=handles[0]
comp_class=unreal.JadeShatterSwitcherComponent
sub_params=unreal.AddNewSubobjectParams(parent_handle=root_handle, new_class=comp_class, blueprint_context=bp)
new_handle, fail = sds.add_new_subobject(sub_params)
if fail and not fail.is_empty():
    log("add_new_subobject FAIL: {}".format(fail))
else:
    sds.rename_subobject(new_handle, unreal.Text("JadeShatter"))
    log("added JadeShatterSwitcherComponent")

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(full)
log("compiled+saved DONE")
