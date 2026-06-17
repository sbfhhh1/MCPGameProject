import unreal

mel = unreal.MaterialEditingLibrary
unreal.log("[Probe] MEL express methods=" + str([x for x in dir(mel) if "express" in x.lower()]))

mat = unreal.load_asset("/Game/TransformationVFX/Material/ObjectMaterial/M_Chair_Dissolve")
unreal.log(f"[Probe] mat type={type(mat).__name__}")

# Try MEL helper to enumerate
for meth in ("get_all_referenced_expressions",):
    fn = getattr(mel, meth, None)
    if fn:
        try:
            res = fn(mat)
            unreal.log(f"[Probe] {meth} -> count={len(list(res))}")
        except Exception as e:
            unreal.log_warning(f"[Probe] {meth} err {e}")

# editor_only_data probe
try:
    eod = mat.get_editor_property("editor_only_data")
    unreal.log(f"[Probe] eod type={type(eod).__name__} val={eod}")
    if eod:
        for prop in ("expression_collection", "expressions"):
            try:
                v = eod.get_editor_property(prop)
                unreal.log(f"[Probe] eod.{prop} type={type(v).__name__} val={v}")
                try:
                    exprs = v.expressions
                    unreal.log(f"[Probe] eod.{prop}.expressions count={len(list(exprs))}")
                except Exception as e2:
                    unreal.log_warning(f"[Probe] .expressions attr err {e2}")
            except Exception as e:
                unreal.log_warning(f"[Probe] eod.{prop} err {e}")
except Exception as e:
    unreal.log_warning(f"[Probe] eod err {e}")

# direct on material
for prop in ("expressions", "expression_collection"):
    try:
        v = mat.get_editor_property(prop)
        unreal.log(f"[Probe] mat.{prop} type={type(v).__name__} count?={v}")
    except Exception as e:
        unreal.log_warning(f"[Probe] mat.{prop} err {e}")

unreal.log("[Probe] DONE")
