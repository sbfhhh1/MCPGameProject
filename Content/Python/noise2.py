import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    # 用expressions属性直接获取所有表达式
    try:
        exprs = mat.get_editor_property("expressions")
        r["total"] = len(exprs) if exprs else 0
        
        noise_info = []
        clamp_info = []
        
        if exprs:
            for e in exprs:
                cn = e.get_class().get_name()
                if "Noise" in cn:
                    info = {"name": e.get_name(), "class": cn}
                    try:
                        info["noise_function"] = str(e.get_editor_property("noise_function"))
                    except: pass
                    noise_info.append(info)
                elif "Clamp" in cn:
                    info = {"name": e.get_name(), "class": cn}
                    try:
                        info["clamp_mode"] = str(e.get_editor_property("clamp_mode"))
                    except: pass
                    try:
                        info["min_default"] = e.get_editor_property("min_default")
                    except: pass
                    try:
                        info["max_default"] = e.get_editor_property("max_default")
                    except: pass
                    clamp_info.append(info)
        
        r["noise"] = noise_info
        r["clamp"] = clamp_info
        
    except Exception as e:
        r["err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "noise2.json"), "w") as f:
    json.dump(r, f, indent=2)
