import unreal


def get_expressions(mat):
    for getter in (
        lambda m: list(m.get_editor_property("editor_only_data").get_editor_property("expression_collection").expressions),
        lambda m: list(m.get_editor_property("editor_only_data").get_editor_property("expressions")),
        lambda m: list(m.get_editor_property("expression_collection").expressions),
        lambda m: list(m.get_editor_property("expressions")),
    ):
        try:
            exprs = getter(mat)
            if exprs:
                return exprs
        except Exception:
            continue
    return []


def expr_label(e):
    if e is None:
        return "None"
    cn = e.get_class().get_name().replace("MaterialExpression", "")
    for prop in ("parameter_name", "constant", "r"):
        try:
            v = e.get_editor_property(prop)
            if v not in (None, ""):
                return f"{cn}({prop}={v})"
        except Exception:
            pass
    try:
        tex = e.get_editor_property("texture")
        if tex:
            return f"{cn}(tex={tex.get_name()})"
    except Exception:
        pass
    return cn


def dump(path):
    asset = unreal.load_asset(path)
    if not asset:
        unreal.log_warning(f"[DG] MISSING {path}")
        return
    mat = asset
    if isinstance(asset, unreal.MaterialInstanceConstant):
        mat = asset.get_editor_property("parent")
    if not mat:
        return
    unreal.log(f"[DG] ===== {mat.get_name()} =====")
    eod = None
    try:
        eod = mat.get_editor_property("editor_only_data")
    except Exception:
        pass
    # property->expression connections
    if eod:
        for prop in ("opacity_mask", "base_color", "subsurface_color", "emissive_color"):
            try:
                inp = eod.get_editor_property(prop)
                expr = inp.get_editor_property("expression")
                if expr:
                    unreal.log(f"[DG] {prop} <- {expr_label(expr)}")
            except Exception:
                pass
    exprs = get_expressions(mat)
    unreal.log(f"[DG] expr_count={len(exprs)}")
    for e in exprs:
        label = expr_label(e)
        inputs = []
        try:
            for ip in e.get_editor_property("input"):
                pass
        except Exception:
            pass
        # try common single 'input'
        for in_prop in ("input", "a", "b"):
            try:
                inp = e.get_editor_property(in_prop)
                ex = inp.get_editor_property("expression")
                if ex:
                    inputs.append(f"{in_prop}<-{expr_label(ex)}")
            except Exception:
                pass
        suffix = (" | " + ", ".join(inputs)) if inputs else ""
        unreal.log(f"[DG]   {label}{suffix}")


for p in [
    "/Game/TransformationVFX/Material/ObjectMaterial/M_Chair_Dissolve",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeFade",
]:
    dump(p)

unreal.log("[DG] DONE")
