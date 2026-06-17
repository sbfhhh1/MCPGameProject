# -*- coding: utf-8 -*-
"""
一键还原：Cell Fracture + Geometry Nodes 消散特效 (Disintegration)
==================================================================
严格还原 YouTube 短片 6V-dhmXqqKs 的破碎规律：
  一尊模型整体保持完整，上半部表面不断碎裂成发光青色小碎块，
  碎块脱离表面 → 向外+向上飘散 → 翻滚旋转 → 缩小消失，飞行时发青光；
  碎裂区是一道沿高度的"阈值波"，由噪声扰动、来回脉动(碎裂↔重组循环)；
  模型整体缓慢转台旋转。

运动法则(逐碎块)：
  field  = (1-归一化高度)*0.8 + 噪声*0.2      # 越靠上 field 越小 → 越先消散
  p(进度)= smoothstep(clamp((T - field)/Band, 0,1))   # T=动画阈值; 0=完整, 1=消散殆尽
  位置    = 中心 + 飞散方向 * FlyDist * p             # 向外(径向)+向上+噪声扰动
  旋转    = 随机欧拉 * p * Spin                       # 翻滚
  缩放    = 1 - p                                     # 缩小消失
  发光    = clamp(p*3,0,1)                            # 脱离瞬间即点亮青色

用法：在 Blender 5.1 脚本工作区打开本文件 → 运行(Alt+P) → 按播放。
      想用自己的模型：先在场景里选中那个网格物体再运行(脚本优先用选中物体)；
      或把 SRC_OBJECT 设为物体名。
"""

import bpy
import bmesh
from mathutils import Vector
import math
import random

# ======================== 配置区 CONFIG ========================
SRC_OBJECT    = ""            # 指定源物体名；留空=用选中网格，否则回退到 Suzanne
OBJ_SCALE     = 2.0           # 占位模型尺寸(用自己的模型时忽略)
FRACTURE_NUM  = 520           # 碎块数量(越多碎得越细)
DISSOLVE_TOP  = 0.55          # 阈值最大值(只消散 field<此值的区域 → 限制在上半部)

FRAME_START   = 1
FRAME_END     = 120           # 24fps ≈ 5s，与原视频一致
FPS           = 24

# —— 以下为几何节点暴露的可调外观参数默认值 ——
BAND          = 0.18          # 消散过渡带宽度(碎块同时在飞的范围)
FLY_DIST      = 1.6           # 飞散距离
UP_BIAS       = 0.6           # 向上飘的偏置
TURBULENCE    = 0.5           # 飞散方向的噪声扰动
SPIN          = 3.0           # 翻滚强度
GLOW_BOOST    = 6.0           # 青色自发光强度
NOISE_SCALE   = 2.5           # 飞散方向噪声的频率

GLOW_COLOR    = (0.0, 0.85, 1.0, 1.0)   # 青色
RANDOM_SEED   = 7
# ==============================================================

random.seed(RANDOM_SEED)
FRACTURE_COLL_NAME = "Shards"


# ------------------------- 场景/源模型 -------------------------
def clean_scene(keep=None):
    """清空场景(除 keep 物体外)，并清理残留数据块/集合。"""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        if o is not keep:
            bpy.data.objects.remove(o, do_unlink=True)
    for cname in (FRACTURE_COLL_NAME, "A_cells"):
        c = bpy.data.collections.get(cname)
        if c:
            bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.node_groups, bpy.data.materials,
                  bpy.data.curves):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def get_source():
    """SRC_OBJECT 指定则用它(保留)，否则全清场景并建 Suzanne 占位。"""
    if SRC_OBJECT and SRC_OBJECT in bpy.data.objects:
        obj = bpy.data.objects[SRC_OBJECT]
        clean_scene(keep=obj)
    else:
        clean_scene()
        bpy.ops.mesh.primitive_monkey_add(size=2.0)
        obj = bpy.context.object
        m = obj.modifiers.new("sub", 'SUBSURF')
        m.subdivision_type = 'SIMPLE'; m.levels = 2   # 加密，碎块更细
        bpy.ops.object.modifier_apply(modifier=m.name)
        obj.name = "Source"
        obj.scale = (OBJ_SCALE * 0.55,) * 3

    # 应用变换，保证后续按世界坐标处理
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


# ------------------------- Voronoi 破碎 -------------------------
def fracture_voronoi(src):
    """手写 Voronoi 破碎(Blender 5.1 无 Cell Fracture 插件)。每块封闭、原点居中。"""
    KNN = 11
    src_bm = bmesh.new()
    src_bm.from_mesh(src.data)
    coords = [v.co.copy() for v in src_bm.verts]
    minc = Vector(tuple(min(c[i] for c in coords) for i in range(3)))
    maxc = Vector(tuple(max(c[i] for c in coords) for i in range(3)))
    center = (minc + maxc) * 0.5
    half = (maxc - minc) * 0.5

    seeds = []
    while len(seeds) < FRACTURE_NUM:
        seeds.append(Vector(tuple(
            center[i] + random.uniform(-half[i], half[i]) for i in range(3))))

    def knn(i):
        order = sorted(range(len(seeds)), key=lambda j: (seeds[j] - seeds[i]).length)
        return [j for j in order if j != i][:KNN]

    coll = bpy.data.collections.new(FRACTURE_COLL_NAME)
    bpy.context.scene.collection.children.link(coll)

    pieces = []
    for i, s in enumerate(seeds):
        bm = src_bm.copy()
        for j in knn(i):
            no = seeds[j] - s
            if no.length < 1e-6:
                continue
            no.normalize()
            co = (seeds[j] + s) * 0.5
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6,
                                         plane_co=co, plane_no=no, clear_outer=True)
            cut_edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            if cut_edges:
                bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)
        if len(bm.faces) == 0:
            bm.free()
            continue
        centroid = Vector((0, 0, 0))
        for v in bm.verts:
            centroid += v.co
        centroid /= len(bm.verts)
        for v in bm.verts:
            v.co -= centroid
        me = bpy.data.meshes.new("S_%04d" % len(pieces))
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("S_%04d" % len(pieces), me)
        ob.location = centroid
        coll.objects.link(ob)
        pieces.append(ob)

    src_bm.free()
    bpy.data.objects.remove(src, do_unlink=True)
    coll.hide_render = True
    coll.hide_viewport = True
    return pieces, coll


# ------------------------- 烘焙碎块属性 -------------------------
def bake_points(pieces):
    """点云：顶点=碎块中心，属性 field(消散排序场)、seed(随机)。"""
    centers = [p.location.copy() for p in pieces]
    zmin = min(c.z for c in centers)
    zmax = max(c.z for c in centers)
    zspan = max(zmax - zmin, 1e-6)

    fields, seeds = [], []
    for c in centers:
        nz = (c.z - zmin) / zspan                 # 0底 1顶
        field = (1.0 - nz) * 0.8 + random.random() * 0.2   # 越靠上越先消散
        fields.append(field)
        seeds.append(random.random())

    mesh = bpy.data.meshes.new("DisintegrateRig_mesh")
    mesh.from_pydata([list(c) for c in centers], [], [])
    mesh.update()
    a_f = mesh.attributes.new("field", 'FLOAT', 'POINT')
    a_s = mesh.attributes.new("seed",  'FLOAT', 'POINT')
    for i in range(len(centers)):
        a_f.data[i].value = fields[i]
        a_s.data[i].value = seeds[i]

    obj = bpy.data.objects.new("DisintegrateRig", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ------------------------- 几何节点 -------------------------
IN_THRESH = "Threshold"
IN_BAND   = "Band"
IN_FLY    = "Fly Dist"
IN_UP     = "Up Bias"
IN_TURB   = "Turbulence"
IN_SPIN   = "Spin"
IN_GLOW   = "Glow Boost"
IN_NSCALE = "Noise Scale"


def build_geo_nodes(coll):
    ng = bpy.data.node_groups.new("DisintegrateGN", 'GeometryNodeTree')
    iface = ng.interface

    def in_float(name, default, lo, hi):
        s = iface.new_socket(name, in_out='INPUT', socket_type='NodeSocketFloat')
        s.default_value = default; s.min_value = lo; s.max_value = hi
        return s

    iface.new_socket("Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
    iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    in_float(IN_THRESH, 0.0, 0.0, 1.0)
    in_float(IN_BAND,   BAND, 0.01, 1.0)
    in_float(IN_FLY,    FLY_DIST, 0.0, 10.0)
    in_float(IN_UP,     UP_BIAS, -2.0, 2.0)
    in_float(IN_TURB,   TURBULENCE, 0.0, 3.0)
    in_float(IN_SPIN,   SPIN, 0.0, 10.0)
    in_float(IN_GLOW,   GLOW_BOOST, 0.0, 30.0)
    in_float(IN_NSCALE, NOISE_SCALE, 0.0, 20.0)

    nodes, links = ng.nodes, ng.links
    pi = math.pi

    def add(t, **props):
        n = nodes.new(t)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def mop(op, a=None, b=None, av=None, bv=None):
        n = add('ShaderNodeMath', operation=op)
        if a is not None: links.new(a, n.inputs[0])
        if av is not None: n.inputs[0].default_value = av
        if b is not None: links.new(b, n.inputs[1])
        if bv is not None: n.inputs[1].default_value = bv
        return n.outputs["Value"]

    def vop(op, a=None, b=None, scale=None):
        n = add('ShaderNodeVectorMath', operation=op)
        if a is not None: links.new(a, n.inputs[0])
        if b is not None: links.new(b, n.inputs[1])
        if scale is not None: links.new(scale, n.inputs["Scale"])
        return n

    n_in  = add('NodeGroupInput')
    n_out = add('NodeGroupOutput')
    n_index = add('GeometryNodeInputIndex')
    n_pos   = add('GeometryNodeInputPosition')

    n_field = add('GeometryNodeInputNamedAttribute', data_type='FLOAT')
    n_field.inputs["Name"].default_value = "field"

    thr  = n_in.outputs[IN_THRESH]
    band = n_in.outputs[IN_BAND]
    fly  = n_in.outputs[IN_FLY]
    up   = n_in.outputs[IN_UP]
    turb = n_in.outputs[IN_TURB]
    spin = n_in.outputs[IN_SPIN]
    glow_b = n_in.outputs[IN_GLOW]
    nscale = n_in.outputs[IN_NSCALE]

    # p = smoothstep( (Threshold - field) / Band )
    raw = mop('DIVIDE', a=mop('SUBTRACT', a=thr, b=n_field.outputs["Attribute"]), b=band)
    n_p = add('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='SMOOTHSTEP')
    links.new(raw, n_p.inputs["Value"])
    p = n_p.outputs["Result"]

    # 飞散方向 dir = normalize( 径向(XY) + 上偏 + 噪声扰动 )
    n_radial = vop('MULTIPLY', a=n_pos.outputs["Position"])
    n_radial.inputs[1].default_value = (1.0, 1.0, 0.0)   # 去掉 z → 水平径向
    n_radial_n = vop('NORMALIZE', a=n_radial.outputs["Vector"])
    # 上向量 * UpBias
    n_upv = add('ShaderNodeCombineXYZ'); links.new(up, n_upv.inputs["Z"])
    # 噪声方向
    n_noise = add('ShaderNodeTexNoise', noise_dimensions='3D')
    links.new(n_pos.outputs["Position"], n_noise.inputs["Vector"])
    links.new(nscale, n_noise.inputs["Scale"])
    n_ncentered = vop('SUBTRACT', a=n_noise.outputs["Color"])  # 噪声-0.5 → 有正负
    n_ncentered.inputs[1].default_value = (0.5, 0.5, 0.5)
    n_nturb = vop('SCALE', a=n_ncentered.outputs["Vector"], scale=turb)
    n_dir = vop('ADD', a=n_radial_n.outputs["Vector"], b=n_upv.outputs["Vector"])
    n_dir2 = vop('ADD', a=n_dir.outputs["Vector"], b=n_nturb.outputs["Vector"])
    n_dirn = vop('NORMALIZE', a=n_dir2.outputs["Vector"])

    # 位移 = dir * FlyDist * p
    n_off = vop('SCALE', a=n_dirn.outputs["Vector"], scale=mop('MULTIPLY', a=fly, b=p))
    n_setpos = add('GeometryNodeSetPosition')
    links.new(n_in.outputs["Geometry"], n_setpos.inputs["Geometry"])
    links.new(n_off.outputs["Vector"], n_setpos.inputs["Offset"])

    # 旋转 = 随机欧拉 * p * Spin
    n_rand = add('FunctionNodeRandomValue', data_type='FLOAT_VECTOR')
    n_rand.inputs[0].default_value = (-pi, -pi, -pi)
    n_rand.inputs[1].default_value = ( pi,  pi,  pi)
    links.new(n_index.outputs["Index"], n_rand.inputs["ID"])
    n_spinvec = vop('SCALE', a=n_rand.outputs["Value"], scale=mop('MULTIPLY', a=p, b=spin))
    n_e2r = add('FunctionNodeEulerToRotation')
    links.new(n_spinvec.outputs["Vector"], n_e2r.inputs[0])

    # 缩放 = 1 - p
    n_scale = mop('SUBTRACT', av=1.0, b=p)

    # 发光 glow = clamp(p*3,0,1) → 存到点上(随实例化+realize 传到材质)
    glow = mop('MINIMUM', a=mop('MULTIPLY', a=p, bv=3.0), bv=1.0)
    n_store = add('GeometryNodeStoreNamedAttribute', data_type='FLOAT', domain='POINT')
    n_store.inputs["Name"].default_value = "glow"
    links.new(n_setpos.outputs["Geometry"], n_store.inputs["Geometry"])
    links.new(glow, n_store.inputs["Value"])

    # 实例化碎块
    n_coll = add('GeometryNodeCollectionInfo', transform_space='RELATIVE')
    n_coll.inputs["Collection"].default_value = coll
    n_coll.inputs["Separate Children"].default_value = True
    n_coll.inputs["Reset Children"].default_value = True
    n_iop = add('GeometryNodeInstanceOnPoints')
    links.new(n_store.outputs["Geometry"], n_iop.inputs["Points"])
    links.new(n_coll.outputs["Instances"], n_iop.inputs["Instance"])
    n_iop.inputs["Pick Instance"].default_value = True
    links.new(n_index.outputs["Index"], n_iop.inputs["Instance Index"])
    links.new(n_e2r.outputs["Rotation"], n_iop.inputs["Rotation"])
    links.new(n_scale, n_iop.inputs["Scale"])

    # realize → glow 属性落到几何上供材质读取
    n_real = add('GeometryNodeRealizeInstances')
    links.new(n_iop.outputs["Instances"], n_real.inputs["Geometry"])
    links.new(n_real.outputs["Geometry"], n_out.inputs["Geometry"])
    return ng


# ------------------------- 材质 -------------------------
def setup_material(pieces):
    """白色大理石 + 由 glow 属性驱动的青色自发光。"""
    mat = bpy.data.materials.new("DisintegrateMat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.92, 1.0)
    if "Roughness" in bsdf.inputs: bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Emission Color"].default_value = GLOW_COLOR

    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = "glow"
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = GLOW_BOOST
    nt.links.new(attr.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs["Value"], bsdf.inputs["Emission Strength"])

    for p in pieces:
        p.data.materials.clear()
        p.data.materials.append(mat)


# ------------------------- 修改器 + 动画 -------------------------
def _sid(ng, name):
    for it in ng.interface.items_tree:
        if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.name == name:
            return it.identifier
    raise RuntimeError("缺少接口:%s" % name)


def apply_and_animate(rig, ng):
    mod = rig.modifiers.new("Disintegrate", 'NODES')
    mod.node_group = ng
    tid = _sid(ng, IN_THRESH)

    def key(frame, val):
        mod[tid] = val
        mod.keyframe_insert(data_path='["%s"]' % tid, frame=frame)

    # 阈值来回脉动：消散↔重组，限制在上半部(峰值=DISSOLVE_TOP)
    span = FRAME_END - FRAME_START
    key(FRAME_START, 0.0)
    key(FRAME_START + int(span * 0.25), DISSOLVE_TOP)
    key(FRAME_START + int(span * 0.50), 0.0)
    key(FRAME_START + int(span * 0.75), DISSOLVE_TOP)
    key(FRAME_END, 0.0)

    # 转台旋转：整体缓慢转(默认插值即可，匀速感足够)
    rig.rotation_euler = (0, 0, 0)
    rig.keyframe_insert(data_path="rotation_euler", frame=FRAME_START)
    rig.rotation_euler = (0, 0, math.radians(120))
    rig.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
    return mod


# ------------------------- 场景/渲染 -------------------------
def setup_scene():
    scn = bpy.context.scene
    scn.frame_start = FRAME_START
    scn.frame_end = FRAME_END
    scn.render.fps = FPS
    scn.frame_set(FRAME_START)

    bpy.ops.object.camera_add(location=(0, -8.5, 1.0),
                              rotation=(math.radians(86), 0, 0))
    scn.camera = bpy.context.object
    bpy.ops.object.light_add(type='AREA', location=(3, -5, 5))
    bpy.context.object.data.energy = 800
    bpy.context.object.data.size = 6

    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.01, 0.01, 0.012, 1.0)
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'

    _setup_bloom(scn)


def _setup_bloom(scn):
    """合成器 Glare(Bloom) 给青色自发光加辉光halo。不同 Blender 版本 API 不同，尽力而为。"""
    try:
        ctree = None
        if hasattr(scn, "compositing_node_group"):       # Blender 5.x
            ng = bpy.data.node_groups.new("Compositor", 'CompositorNodeTree')
            scn.compositing_node_group = ng
            ctree = ng
        else:                                             # 旧版
            scn.use_nodes = True
            ctree = scn.node_tree
        for n in list(ctree.nodes):
            ctree.nodes.remove(n)
        rl = ctree.nodes.new('CompositorNodeRLayers')
        glare = ctree.nodes.new('CompositorNodeGlare')
        glare.glare_type = 'BLOOM'
        glare.threshold = 0.6
        if hasattr(glare, "size"):
            glare.size = 8
        comp = ctree.nodes.new('CompositorNodeComposite')
        ctree.links.new(rl.outputs["Image"], glare.inputs["Image"])
        ctree.links.new(glare.outputs["Image"], comp.inputs["Image"])
    except Exception as e:
        print("Bloom 跳过(版本不兼容):", e)


def main():
    src = get_source()   # 内部按 SRC_OBJECT 决定清场策略
    pieces, coll = fracture_voronoi(src)
    print("碎块数量:", len(pieces))
    rig = bake_points(pieces)
    setup_material(pieces)
    ng = build_geo_nodes(coll)
    apply_and_animate(rig, ng)
    setup_scene()
    print("✅ 完成！按播放查看：模型上半部碎裂成青色碎块飞散消失，循环脉动+转台旋转。")


if __name__ == "__main__":
    main()
