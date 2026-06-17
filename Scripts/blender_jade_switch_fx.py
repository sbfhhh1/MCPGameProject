# -*- coding: utf-8 -*-
"""
玉石模型破碎切换 (Geometry Nodes) —— 面向 UE 实时切换
=====================================================
还原参考视频"两尊雕像通过破碎动画过渡"的规律，并改造成可在 UE 实时驱动的形态：
  · 场景内置 3 个模型(默认 Cube / Sphere / Suzanne 占位，将来换成玉石模型)
  · 几何节点只对外暴露一个 float "Model Index"(0/1/2)
  · floor(Index)=当前模型 A，floor(Index)+1=下一模型 B，frac(Index)=过渡进度 t
  · t:0→1 时 A 从顶部消散、B 从顶部生成，接缝处由噪声扰动成破碎边、
    迸发青色发光小方块向外飞散 —— 即"破碎过渡"
  · 运行时把 Model Index 从任意当前值 lerp 到目标整数，即可过渡到目标模型

UE 管线适配(见 unreal_gn_eval.py)：
  · UE 只按名字设数值输入(modifier[key]=value) → 模型内置在 GN，只暴露 float
  · 逐帧把 GN realize 成网格导出 → 本 GN 末尾 Realize Instances
  · 发光碎块用独立材质槽(Set Material) → UE 按 material_index 区分玉石/发光

用法：Blender 5.1 脚本工作区打开 → 运行(Alt+P) → 播放看自动 0→1→2→0 循环演示；
      UE 中导入后改 "Model Index" 这个 float 即可实时切换。
"""

import bpy
import math
import random
from mathutils import Vector

# ======================== 配置区 CONFIG ========================
MODEL_KINDS = ["CUBE", "ICOSPHERE", "MONKEY"]   # 3 个占位模型
MODEL_HALF  = 1.0          # 归一化半高(所有模型缩放到 z∈[-MODEL_HALF, MODEL_HALF])

FRAME_START = 1
FRAME_END   = 160
FPS         = 24

# —— 几何节点暴露的可调参数默认值 ——
SEAM_WIDTH  = 0.14         # 破碎接缝带宽度
NOISE_SCALE = 3.5          # 接缝噪声频率(越大碎边越细)
NOISE_AMP   = 0.18         # 接缝噪声扰动幅度
FRAG_DENS   = 250.0        # 碎块密度
FRAG_SIZE   = 0.06         # 碎块方块大小
FLY_DIST    = 0.5          # 碎块向外飞散距离
GLOW_BOOST  = 9.0          # 青色自发光强度

JADE_COLOR  = (0.20, 0.75, 0.55, 1.0)   # 玉石绿(占位)
GLOW_COLOR  = (0.0, 0.9, 1.0, 1.0)      # 青色破碎光
RANDOM_SEED = 7
# ==============================================================

random.seed(RANDOM_SEED)
IN_INDEX  = "Model Index"
IN_SEAM   = "Seam Width"
IN_NSCALE = "Noise Scale"
IN_NAMP   = "Noise Amp"
IN_FDENS  = "Frag Density"
IN_FSIZE  = "Frag Size"
IN_FLY    = "Fly Dist"
IN_GLOW   = "Glow Boost"


# ------------------------- 场景/模型 -------------------------
def clean_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.node_groups, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def _normalize(obj):
    """缩放/居中到 z∈[-MODEL_HALF, MODEL_HALF]，并应用变换。"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zs = [v.z for v in bb]
    xs = [v.x for v in bb]; ys = [v.y for v in bb]
    cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2; cz = (min(zs) + max(zs)) / 2
    half = max(max(zs) - min(zs), max(xs) - min(xs), max(ys) - min(ys)) / 2
    s = MODEL_HALF / max(half, 1e-6)
    obj.location = (-cx * s, -cy * s, -cz * s)
    obj.scale = (s, s, s)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def make_models():
    """创建 3 个占位模型(已归一化、加密、贴玉石材质)，隐藏，仅供 GN 引用。"""
    jade = bpy.data.materials.new("Jade")
    jade.use_nodes = True
    b = jade.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = JADE_COLOR
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value = 0.25
    if "Metallic" in b.inputs: b.inputs["Metallic"].default_value = 0.1

    models = []
    for i, kind in enumerate(MODEL_KINDS):
        if kind == "CUBE":
            bpy.ops.mesh.primitive_cube_add(size=2.0)
            o = bpy.context.object
            m = o.modifiers.new("s", 'SUBSURF'); m.subdivision_type = 'SIMPLE'; m.levels = 4
            bpy.ops.object.modifier_apply(modifier=m.name)
        elif kind == "ICOSPHERE":
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
            o = bpy.context.object
        else:  # MONKEY
            bpy.ops.mesh.primitive_monkey_add(size=2.0)
            o = bpy.context.object
            m = o.modifiers.new("s", 'SUBSURF'); m.subdivision_type = 'SIMPLE'; m.levels = 2
            bpy.ops.object.modifier_apply(modifier=m.name)
        o.name = "Model_%d_%s" % (i, kind)
        _normalize(o)
        o.data.materials.clear()
        o.data.materials.append(jade)
        o.hide_render = True
        o.hide_viewport = True
        models.append(o)
    return models, jade


# ------------------------- 几何节点 -------------------------
def build_gn(models, glow_mat):
    ng = bpy.data.node_groups.new("JadeSwitchGN", 'GeometryNodeTree')
    iface = ng.interface

    def in_float(name, d, lo, hi):
        s = iface.new_socket(name, in_out='INPUT', socket_type='NodeSocketFloat')
        s.default_value = d; s.min_value = lo; s.max_value = hi
        return s

    iface.new_socket("Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
    iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    in_float(IN_INDEX,  0.0, 0.0, len(models) - 1)
    in_float(IN_SEAM,   SEAM_WIDTH, 0.01, 0.5)
    in_float(IN_NSCALE, NOISE_SCALE, 0.0, 20.0)
    in_float(IN_NAMP,   NOISE_AMP, 0.0, 1.0)
    in_float(IN_FDENS,  FRAG_DENS, 0.0, 2000.0)
    in_float(IN_FSIZE,  FRAG_SIZE, 0.001, 0.5)
    in_float(IN_FLY,    FLY_DIST, 0.0, 3.0)
    in_float(IN_GLOW,   GLOW_BOOST, 0.0, 30.0)

    nodes, links = ng.nodes, ng.links
    pi = math.pi

    def add(t, **p):
        n = nodes.new(t)
        for k, v in p.items():
            setattr(n, k, v)
        return n

    def mop(op, a=None, b=None, av=None, bv=None):
        n = add('ShaderNodeMath', operation=op)
        if a is not None: links.new(a, n.inputs[0])
        if av is not None: n.inputs[0].default_value = av
        if b is not None: links.new(b, n.inputs[1])
        if bv is not None: n.inputs[1].default_value = bv
        return n.outputs["Value"]

    n_in  = add('NodeGroupInput')
    n_out = add('NodeGroupOutput')
    idx   = n_in.outputs[IN_INDEX]

    # i0 = floor(Index) (clamp 0..N-1), i1 = clamp(i0+1, 0..N-1), t = Index - i0
    i0f = mop('FLOOR', a=idx)
    i0c = mop('MINIMUM', a=mop('MAXIMUM', a=i0f, bv=0.0), bv=float(len(models) - 1))
    i1c = mop('MINIMUM', a=mop('ADD', a=i0c, bv=1.0), bv=float(len(models) - 1))
    t   = mop('SUBTRACT', a=idx, b=i0c)
    i0_int = add('FunctionNodeFloatToInt', rounding_mode='FLOOR'); links.new(i0c, i0_int.inputs[0])
    i1_int = add('FunctionNodeFloatToInt', rounding_mode='FLOOR'); links.new(i1c, i1_int.inputs[0])

    # 3 个模型几何
    objinfos = []
    for m in models:
        oi = add('GeometryNodeObjectInfo', transform_space='ORIGINAL')
        oi.inputs["Object"].default_value = m
        objinfos.append(oi)

    def index_switch(index_int):
        sw = add('GeometryNodeIndexSwitch', data_type='GEOMETRY')
        while len(sw.index_switch_items) < len(models):
            sw.index_switch_items.new()
        links.new(index_int, sw.inputs["Index"])
        for k, oi in enumerate(objinfos):
            links.new(oi.outputs["Geometry"], sw.inputs[str(k)])
        return sw.outputs["Output"]

    geoA = index_switch(i0_int.outputs["Integer"])
    geoB = index_switch(i1_int.outputs["Integer"])

    # 接缝从"顶部之上"(t=0,无相交→整数态完整)扫到"底部之下"(t=1)
    # margin 让扫描越过 field∈[0,1] 的上下边界(含噪声/带宽余量)
    margin = mop('ADD', a=mop('ADD', a=n_in.outputs[IN_NAMP], b=n_in.outputs[IN_SEAM]), bv=0.05)
    hi  = mop('ADD', av=1.0, b=margin)
    lo  = mop('MULTIPLY', a=margin, bv=-1.0)
    seam = mop('SUBTRACT', a=hi, b=mop('MULTIPLY', a=t, b=mop('SUBTRACT', a=hi, b=lo)))

    # —— field 子树工厂：在调用处的几何上现算 field = z*0.5+0.5 + (noise-0.5)*amp ——
    def field_value():
        pos = add('GeometryNodeInputPosition')
        sep = add('ShaderNodeSeparateXYZ'); links.new(pos.outputs["Position"], sep.inputs["Vector"])
        zf = mop('ADD', a=mop('MULTIPLY', a=sep.outputs["Z"], bv=0.5), bv=0.5)
        noise = add('ShaderNodeTexNoise', noise_dimensions='3D')
        links.new(pos.outputs["Position"], noise.inputs["Vector"])
        links.new(n_in.outputs[IN_NSCALE], noise.inputs["Scale"])
        nz = mop('MULTIPLY', a=mop('SUBTRACT', a=noise.outputs["Factor"], bv=0.5),
                 b=n_in.outputs[IN_NAMP])
        return mop('ADD', a=zf, b=nz)

    # A：删除 field>=seam(顶部先消散)；B：删除 field<seam(只留顶部新生)
    delA = add('GeometryNodeDeleteGeometry', domain='FACE')
    links.new(geoA, delA.inputs["Geometry"])
    links.new(mop('GREATER_THAN', a=field_value(), b=seam), delA.inputs["Selection"])

    delB = add('GeometryNodeDeleteGeometry', domain='FACE')
    links.new(geoB, delB.inputs["Geometry"])
    links.new(mop('LESS_THAN', a=field_value(), b=seam), delB.inputs["Selection"])

    # 碎块：在 A 的接缝带内撒点 → 实例小方块 → 向外飞 + 旋转 + 青光
    band = mop('LESS_THAN',
               a=mop('ABSOLUTE', a=mop('SUBTRACT', a=field_value(), b=seam)),
               b=n_in.outputs[IN_SEAM])
    dist = add('GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM')
    links.new(geoA, dist.inputs["Mesh"])
    links.new(band, dist.inputs["Selection"])
    links.new(n_in.outputs[IN_FDENS], dist.inputs["Density"])

    # 向外飞：沿法线推 FlyDist，外加随机翻滚
    nrm = dist.outputs["Normal"]
    push = add('ShaderNodeVectorMath', operation='SCALE')
    links.new(nrm, push.inputs[0]); links.new(n_in.outputs[IN_FLY], push.inputs["Scale"])
    setp = add('GeometryNodeSetPosition')
    links.new(dist.outputs["Points"], setp.inputs["Geometry"])
    links.new(push.outputs["Vector"], setp.inputs["Offset"])

    rand = add('FunctionNodeRandomValue', data_type='FLOAT_VECTOR')
    rand.inputs[0].default_value = (-pi, -pi, -pi); rand.inputs[1].default_value = (pi, pi, pi)
    idxn = add('GeometryNodeInputIndex'); links.new(idxn.outputs["Index"], rand.inputs["ID"])
    e2r = add('FunctionNodeEulerToRotation'); links.new(rand.outputs["Value"], e2r.inputs[0])

    cube = add('GeometryNodeMeshCube'); links.new(n_in.outputs[IN_FSIZE], cube.inputs["Size"])
    iop = add('GeometryNodeInstanceOnPoints')
    links.new(setp.outputs["Geometry"], iop.inputs["Points"])
    links.new(cube.outputs["Mesh"], iop.inputs["Instance"])
    links.new(e2r.outputs["Rotation"], iop.inputs["Rotation"])
    real = add('GeometryNodeRealizeInstances'); links.new(iop.outputs["Instances"], real.inputs["Geometry"])
    setm = add('GeometryNodeSetMaterial'); setm.inputs["Material"].default_value = glow_mat
    links.new(real.outputs["Geometry"], setm.inputs["Geometry"])

    # 合并：A剩余 + B新生 + 碎块
    join = add('GeometryNodeJoinGeometry')
    links.new(delA.outputs["Geometry"], join.inputs["Geometry"])
    links.new(delB.outputs["Geometry"], join.inputs["Geometry"])
    links.new(setm.outputs["Geometry"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], n_out.inputs["Geometry"])
    return ng


# ------------------------- 材质 -------------------------
def make_glow_mat():
    mat = bpy.data.materials.new("FractureGlow")
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = GLOW_COLOR
    b.inputs["Emission Color"].default_value = GLOW_COLOR
    b.inputs["Emission Strength"].default_value = GLOW_BOOST
    return mat


# ------------------------- 修改器 + 演示动画 -------------------------
def _sid(ng, name):
    for it in ng.interface.items_tree:
        if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.name == name:
            return it.identifier
    raise RuntimeError("缺少接口:%s" % name)


def apply_and_animate(host, ng):
    mod = host.modifiers.new("JadeSwitch", 'NODES')
    mod.node_group = ng
    iid = _sid(ng, IN_INDEX)

    def key(frame, val):
        mod[iid] = val
        mod.keyframe_insert(data_path='["%s"]' % iid, frame=frame)

    # 演示：0→(过渡)→1→(过渡)→2→(过渡)→0，整数处停留展示完整模型
    key(1, 0.0); key(25, 0.0)
    key(55, 1.0); key(80, 1.0)
    key(110, 2.0); key(135, 2.0)
    key(160, 0.0)
    return mod


def setup_scene(host):
    scn = bpy.context.scene
    scn.frame_start = FRAME_START; scn.frame_end = FRAME_END
    scn.render.fps = FPS; scn.frame_set(FRAME_START)

    bpy.ops.object.camera_add(location=(0, -6.5, 0.6), rotation=(math.radians(88), 0, 0))
    scn.camera = bpy.context.object
    bpy.ops.object.light_add(type='AREA', location=(3, -4, 5))
    bpy.context.object.data.energy = 700; bpy.context.object.data.size = 6

    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world; world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg: bg.inputs[0].default_value = (0.012, 0.012, 0.015, 1.0)
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'


def main():
    clean_scene()
    models, jade = make_models()
    glow = make_glow_mat()
    ng = build_gn(models, glow)
    host = bpy.data.objects.new("JadeSwitch", bpy.data.meshes.new("JadeSwitch_mesh"))
    bpy.context.scene.collection.objects.link(host)
    apply_and_animate(host, ng)
    setup_scene(host)
    print("✅ 完成！播放看 0→1→2→0 破碎切换；UE 中改 'Model Index' float 实时切换。")


if __name__ == "__main__":
    main()
