import unreal

mel = unreal.MaterialEditingLibrary
MAT = "/Game/TransformationVFX/Material/ObjectMaterial/M_Chair_Dissolve"
MI = "/Game/TransformationVFX/Material/ObjectMaterial/MI_Chair_UniversalDissolve"

mat = unreal.load_asset(MAT)
mi = unreal.load_asset(MI)

scalars = ["Dissolve Amount", "Cheap Contrast", "Power", "Texture Size", "Contrast",
           "Texture Power", "Amount Divide", "Amount Multiply", "Amount Subtract",
           "Alpha Dither", "Divide Texture", "RoughnessSeats", "RoughnessMetal", "RoughnessBase"]

unreal.log(f"[Chair] clip={mat.get_editor_property('opacity_mask_clip_value')}")
for name in scalars:
    try:
        dv = mel.get_material_default_scalar_parameter_value(mat, name)
        unreal.log(f"[Chair] MAT scalar '{name}' default={dv}")
    except Exception as e:
        unreal.log_warning(f"[Chair] MAT scalar '{name}' err {e}")

# texture default
for tname in ["Dissolve Texture"]:
    try:
        tv = mel.get_material_default_texture_parameter_value(mat, tname)
        unreal.log(f"[Chair] MAT texture '{tname}' default={tv.get_path_name() if tv else None}")
    except Exception as e:
        unreal.log_warning(f"[Chair] MAT texture '{tname}' err {e}")

# instance overrides
if mi:
    for name in scalars:
        try:
            v = mel.get_material_instance_scalar_parameter_value(mi, name)
            unreal.log(f"[Chair] MI scalar '{name}'={v}")
        except Exception:
            pass

unreal.log("[Chair] DONE")
