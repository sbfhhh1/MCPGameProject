import unreal

mel = unreal.MaterialEditingLibrary
MI = "/Game/TransformationVFX/Material/CharactorMaterial/MI_Manny_Particle"

inst = unreal.load_asset(MI)
unreal.log(f"[PMat] loaded={bool(inst)} type={type(inst).__name__}")
if inst:
    parent = inst.get_editor_property("parent")
    unreal.log(f"[PMat] parent={parent.get_path_name() if parent else None}")
    base = parent
    while isinstance(base, unreal.MaterialInstanceConstant):
        base = base.get_editor_property("parent")
    if base:
        unreal.log(f"[PMat] base material={base.get_name()} blend={base.get_editor_property('blend_mode')} "
                   f"shading={base.get_editor_property('shading_model')}")
    try:
        unreal.log(f"[PMat] scalars={list(mel.get_scalar_parameter_names(inst))}")
        unreal.log(f"[PMat] vectors={list(mel.get_vector_parameter_names(inst))}")
    except Exception as e:
        unreal.log_warning(f"[PMat] param err {e}")

# Niagara system user params
ns = unreal.load_asset("/Game/TransformationVFX/Niagara/NS_Inhalation_SM")
unreal.log(f"[PMat] niagara loaded={bool(ns)}")
try:
    exposed = ns.get_exposed_parameters() if hasattr(ns, "get_exposed_parameters") else None
    unreal.log(f"[PMat] niagara get_exposed_parameters={exposed}")
except Exception as e:
    unreal.log_warning(f"[PMat] niagara params err {e}")

unreal.log("[PMat] DONE")
