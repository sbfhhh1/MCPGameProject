import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    # 找到Noise节点并检查属性
    num = unreal.MaterialEditingLibrary.get_num_material_expressions(mat)
    noise_nodes = []
    clamp_nodes = []
    
    for i in range(num):
        expr = unreal.MaterialEditingLibrary.get_material_expression(mat, i)
        cn = expr.get_class().get_name()
        if "Noise" in cn:
            noise_nodes.append({"idx": i, "name": expr.get_name(), "class": cn})
            # 检查输出范围相关属性
            try:
                nf = expr.get_editor_property("noise_function")
                noise_nodes[-1]["noise_function"] = str(nf)
            except: pass
            try:
                ov = expr.get_editor_property("output_value")
                noise_nodes[-1]["output_value"] = str(ov)
            except: pass
            try:
                # levels for fractal
                lv = expr.get_editor_property("levels")
                noise_nodes[-1]["levels"] = lv
            except: pass
        elif "Clamp" in cn:
            clamp_nodes.append({"idx": i, "name": expr.get_name(), "class": cn})
            try:
                cm = expr.get_editor_property("clamp_mode")
                clamp_nodes[-1]["clamp_mode"] = str(cm)
            except: pass
            try:
                mind = expr.get_editor_property("min_default")
                clamp_nodes[-1]["min_default"] = mind
            except: pass
            try:
                maxd = expr.get_editor_property("max_default")
                clamp_nodes[-1]["max_default"] = maxd
            except: pass
    
    r["noise_nodes"] = noise_nodes
    r["clamp_nodes"] = clamp_nodes

with open(os.path.join(os.environ["USERPROFILE"], "noise_check.json"), "w") as f:
    json.dump(r, f, indent=2)
