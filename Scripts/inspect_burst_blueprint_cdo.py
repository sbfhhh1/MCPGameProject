import unreal


BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
CLASS_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM.BP_Burst_SM_C"

bp = unreal.load_asset(BP_PATH)
generated_class = unreal.load_class(None, CLASS_PATH)
cdo = unreal.get_default_object(generated_class)
unreal.log(f"[BurstCDO] Class={generated_class} CDO={cdo}")

for component in cdo.get_components_by_class(unreal.ActorComponent):
    unreal.log(f"[BurstCDO] Component={component.get_name()} Class={component.get_class().get_name()}")
    if isinstance(component, unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        unreal.log(
            f"[BurstCDO] StaticMesh={mesh.get_path_name() if mesh else 'None'} "
            f"Relative={component.get_relative_transform()}")
