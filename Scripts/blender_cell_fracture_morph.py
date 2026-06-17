# -*- coding: utf-8 -*-
"""
一键还原：Cell Fracture + Geometry Nodes 变形动画
=================================================
效果：源物体 A(球) 被"细胞破碎(Cell Fracture)"成大量碎块，
     再由几何节点驱动这些碎块飞散、旋转，最终重组成目标物体 B(猴头 Suzanne)。
     —— 复刻 YouTube 短片 "Morph object in Blender using Geometry Nodes"

用法：在 Blender 5.1 里打开"脚本(Scripting)"工作区 → 打开本文件 → 运行(Alt+P)
      运行后直接按空格/播放即可看到变形动画。

实现思路（关键点都在 Python 里预计算，几何节点只做插值，最大化稳定性）：
  1. 生成球 A 和猴头 B。
  2. 用 Cell Fracture 插件把 A 碎成 N 个碎块，每块原点重定位到自身质心。
  3. 对每个碎块：起点 = 它的质心；终点 = 猴头 B 表面上离它最近的点(BVH 最近点)。
     把"起点/终点/随机种子/延迟"烘焙成一个点云物体的顶点属性。
  4. 几何节点：按点索引"挑选实例"把对应碎块放到点上，
     位置 = lerp(起点, 终点, 缓动后的因子)，
     旋转 = 随机欧拉 * sin(pi*t)（飞行途中旋转，首尾归零，落位平整）。
  5. 关键帧驱动 Factor 0→1 完成整段变形。
"""

import bpy
import bmesh
import addon_utils
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import math
import random

# ======================== 配置区 CONFIG ========================
SRC_KIND      = "ICOSPHERE"   # 源物体 A：ICOSPHERE / CUBE
TGT_KIND      = "MONKEY"      # 目标物体 B：MONKEY / TEXT
TGT_TEXT      = "BLENDER"     # 当 TGT_KIND == "TEXT" 时使用的文字
OBJ_SCALE     = 1.4           # 整体尺寸
FRACTURE_NUM  = 180           # 碎块数量(越多越细腻/目标轮廓越清晰，但越慢)
END_SCALE     = 0.8           # 碎块落到目标时的缩放(<1 让重组轮廓更紧致清晰)
FRAME_START   = 1
FRAME_MORPH_A = 20            # 开始变形的帧
FRAME_MORPH_B = 70            # 变形结束的帧
FRAME_END     = 90
STAGGER       = 0.6           # 碎块错峰程度(0=同时动, 接近1=拖尾波浪感强)
SPIN_STRENGTH = 1.0           # 飞行中旋转强度(0=不转)
REVEAL_START  = 0.78          # 尾段揭示开始(Factor 比例)：完整目标模型开始显现
REVEAL_END    = 1.0           # 尾段揭示结束：碎块完全消失、只剩完整目标模型
RANDOM_SEED   = 7
# ==============================================================

random.seed(RANDOM_SEED)
FRACTURE_COLL_NAME = "A_cells"


# ------------------------- 工具函数 -------------------------
def clean_scene():
    """清空场景内的物体、几何节点组、网格数据。"""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.node_groups,
                  bpy.data.curves, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)
    # 删除我们可能残留的碎块集合
    coll = bpy.data.collections.get(FRACTURE_COLL_NAME)
    if coll:
        bpy.data.collections.remove(coll)


def make_source():
    """创建源物体 A。"""
    if SRC_KIND == "CUBE":
        bpy.ops.mesh.primitive_cube_add(size=2.0)
        obj = bpy.context.object
        # 细分一下，碎块更均匀
        m = obj.modifiers.new("sub", 'SUBSURF'); m.subdivision_type = 'SIMPLE'
        m.levels = 2; bpy.ops.object.modifier_apply(modifier=m.name)
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
        obj = bpy.context.object
    obj.name = "Source_A"
    obj.scale = (OBJ_SCALE,) * 3
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj


def make_target():
    """创建目标物体 B，返回一个三角化后的纯网格物体（供 BVH 取最近点）。"""
    if TGT_KIND == "TEXT":
        cur = bpy.data.curves.new("Target_B_txt", type='FONT')
        cur.body = TGT_TEXT
        cur.align_x = 'CENTER'; cur.align_y = 'CENTER'
        obj = bpy.data.objects.new("Target_B", cur)
        bpy.context.collection.objects.link(obj)
        obj.scale = (OBJ_SCALE,) * 3
        # 文字转网格
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        obj = bpy.context.object
    else:
        bpy.ops.mesh.primitive_monkey_add(size=2.0)
        obj = bpy.context.object
        obj.name = "Target_B"
        obj.scale = (OBJ_SCALE,) * 3
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # 三角化，方便最近点采样
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def fracture_voronoi(src):
    """手写 Voronoi 破碎（不依赖任何插件，Blender 5.1 已移除 Cell Fracture 插件）。

    原理 = Cell Fracture 的底层算法：对每个种子点，用它与相邻种子的
    垂直平分面逐个切割源网格，再封盖切口，得到一个封闭的 Voronoi 碎块。
    """
    KNN = 12  # 每个种子参与切割的最近邻数量

    # 源网格 bmesh（变换已应用，matrix 为单位阵，顶点即世界坐标）
    src_bm = bmesh.new()
    src_bm.from_mesh(src.data)
    coords = [v.co.copy() for v in src_bm.verts]
    minc = Vector(tuple(min(c[i] for c in coords) for i in range(3)))
    maxc = Vector(tuple(max(c[i] for c in coords) for i in range(3)))
    center = (minc + maxc) * 0.5
    half = (maxc - minc) * 0.5

    # 包围盒内随机撒种（盒外/空格子的碎块会为空，自动跳过）
    seeds = []
    tries = 0
    while len(seeds) < FRACTURE_NUM and tries < FRACTURE_NUM * 200:
        tries += 1
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
            cut_edges = [e for e in res['geom_cut']
                         if isinstance(e, bmesh.types.BMEdge)]
            if cut_edges:
                bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)  # 封盖切口
        if len(bm.faces) == 0:
            bm.free()
            continue

        # 重定位原点到碎块质心：顶点整体平移 -centroid，物体 location = centroid
        centroid = Vector((0, 0, 0))
        for v in bm.verts:
            centroid += v.co
        centroid /= len(bm.verts)
        for v in bm.verts:
            v.co -= centroid

        me = bpy.data.meshes.new("P_%04d" % len(pieces))
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("P_%04d" % len(pieces), me)
        ob.location = centroid
        coll.objects.link(ob)
        pieces.append(ob)

    src_bm.free()
    # 删除源物体
    bpy.data.objects.remove(src, do_unlink=True)

    # 集合仅作为实例来源，不直接渲染/显示
    coll.hide_render = True
    coll.hide_viewport = True
    return pieces, coll


def sample_surface_points(target, count):
    """在 target 网格表面按面积加权随机采样 count 个世界坐标点。
    这样每个碎块分配一个目标点，能完整覆盖出目标形状（含耳朵等凸出部位）。"""
    import bisect
    mw = target.matrix_world.copy()
    me = target.data
    me.calc_loop_triangles()
    tris = me.loop_triangles
    if not tris:
        return [mw @ v.co for v in me.vertices][:count]

    cum, acc = [], 0.0
    for t in tris:
        acc += t.area
        cum.append(acc)
    total = acc

    pts = []
    for _ in range(count):
        r = random.random() * total
        t = tris[min(bisect.bisect_left(cum, r), len(tris) - 1)]
        a, b, c = (me.vertices[i].co for i in t.vertices)
        u, v = random.random(), random.random()
        if u + v > 1.0:
            u, v = 1.0 - u, 1.0 - v
        pts.append(mw @ (a * (1.0 - u - v) + b * u + c * v))
    return pts


def bake_morph_points(pieces, target):
    """生成点云物体：顶点=碎块质心(起点)，属性 target=终点, seed/delay=随机/错峰。"""
    ends = sample_surface_points(target, len(pieces))

    starts, seeds, delays = [], [], []
    zmin = min(p.location.z for p in pieces)
    zmax = max(p.location.z for p in pieces)
    zspan = max(zmax - zmin, 1e-6)

    for p in pieces:
        # 注意：碎块集合被隐藏后 matrix_world 不会被依赖图刷新，
        # 必须用 .location（未父子化物体的 location 即世界坐标）。
        start = p.location.copy()
        starts.append(start)
        seeds.append(random.random())
        # 按高度从下往上波浪式重组
        delays.append((start.z - zmin) / zspan)

    # 创建点云网格（仅顶点）
    mesh = bpy.data.meshes.new("MorphPoints_mesh")
    mesh.from_pydata([list(s) for s in starts], [], [])
    mesh.update()

    a_t = mesh.attributes.new("target", 'FLOAT_VECTOR', 'POINT')
    a_s = mesh.attributes.new("seed",   'FLOAT',        'POINT')
    a_d = mesh.attributes.new("delay",  'FLOAT',        'POINT')
    for i in range(len(starts)):
        a_t.data[i].vector = ends[i]
        a_s.data[i].value  = seeds[i]
        a_d.data[i].value  = delays[i]

    obj = bpy.data.objects.new("MorphRig", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ------------------------- 几何节点 -------------------------
# 暴露给修改器面板的输入接口名（方便自定义）
IN_FACTOR  = "Factor"
IN_TARGET  = "Target Model"   # 尾段显现的完整目标模型(Object)
IN_SPIN    = "Spin"           # 飞行旋转强度
IN_STAGGER = "Stagger"        # 碎块错峰程度
IN_ENDSC   = "End Scale"      # 碎块落位缩放
IN_RVST    = "Reveal Start"   # 尾段揭示开始
IN_RVEND   = "Reveal End"     # 尾段揭示结束


def build_geo_nodes(coll):
    """构建变形几何节点组：碎块飞行变形 + 尾段揭示完整目标模型。
    所有影响外观的参数都暴露为接口，可在修改器面板里直接调。"""
    ng = bpy.data.node_groups.new("MorphGN", 'GeometryNodeTree')
    iface = ng.interface

    def in_float(name, default, lo, hi):
        s = iface.new_socket(name, in_out='INPUT', socket_type='NodeSocketFloat')
        s.default_value = default; s.min_value = lo; s.max_value = hi
        return s

    iface.new_socket("Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
    iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    in_float(IN_FACTOR, 0.0, 0.0, 1.0)
    iface.new_socket(IN_TARGET, in_out='INPUT', socket_type='NodeSocketObject')
    in_float(IN_SPIN,    SPIN_STRENGTH, 0.0, 5.0)
    in_float(IN_STAGGER, STAGGER,       0.0, 0.95)
    in_float(IN_ENDSC,   END_SCALE,     0.0, 2.0)
    in_float(IN_RVST,    REVEAL_START,  0.0, 1.0)
    in_float(IN_RVEND,   REVEAL_END,    0.0, 1.0)

    nodes = ng.nodes
    links = ng.links
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

    n_in  = add('NodeGroupInput')
    n_out = add('NodeGroupOutput')
    n_index = add('GeometryNodeInputIndex')
    n_pos   = add('GeometryNodeInputPosition')

    n_target = add('GeometryNodeInputNamedAttribute', data_type='FLOAT_VECTOR')
    n_target.inputs["Name"].default_value = "target"
    n_delay  = add('GeometryNodeInputNamedAttribute', data_type='FLOAT')
    n_delay.inputs["Name"].default_value = "delay"

    fac     = n_in.outputs[IN_FACTOR]
    spin    = n_in.outputs[IN_SPIN]
    stagger = n_in.outputs[IN_STAGGER]
    endsc   = n_in.outputs[IN_ENDSC]
    rv_st   = n_in.outputs[IN_RVST]
    rv_end  = n_in.outputs[IN_RVEND]

    # 错峰缓动：ease = smoothstep((Factor - delay*Stagger) / (1-Stagger))
    muld = mop('MULTIPLY', a=n_delay.outputs["Attribute"], b=stagger)
    sub  = mop('SUBTRACT', a=fac, b=muld)
    one_m_stag = mop('SUBTRACT', av=1.0, b=stagger)
    div  = mop('DIVIDE', a=sub, b=one_m_stag)
    n_ease = add('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='SMOOTHSTEP')
    links.new(div, n_ease.inputs["Value"])
    ease = n_ease.outputs["Result"]

    # 位移 offset = (target - position) * ease
    n_subv = add('ShaderNodeVectorMath', operation='SUBTRACT')
    links.new(n_target.outputs["Attribute"], n_subv.inputs[0])
    links.new(n_pos.outputs["Position"], n_subv.inputs[1])
    n_scalev = add('ShaderNodeVectorMath', operation='SCALE')
    links.new(n_subv.outputs["Vector"], n_scalev.inputs[0])
    links.new(ease, n_scalev.inputs["Scale"])
    n_setpos = add('GeometryNodeSetPosition')
    links.new(n_in.outputs["Geometry"], n_setpos.inputs["Geometry"])
    links.new(n_scalev.outputs["Vector"], n_setpos.inputs["Offset"])

    # 旋转：随机欧拉 * sin(pi*ease) * Spin
    n_rand = add('FunctionNodeRandomValue', data_type='FLOAT_VECTOR')
    n_rand.inputs[0].default_value = (-pi, -pi, -pi)
    n_rand.inputs[1].default_value = ( pi,  pi,  pi)
    links.new(n_index.outputs["Index"], n_rand.inputs["ID"])
    sin_e = mop('SINE', a=mop('MULTIPLY', a=ease, bv=pi))
    sink  = mop('MULTIPLY', a=sin_e, b=spin)
    n_spin = add('ShaderNodeVectorMath', operation='SCALE')
    links.new(n_rand.outputs["Value"], n_spin.inputs[0])
    links.new(sink, n_spin.inputs["Scale"])
    n_e2r = add('FunctionNodeEulerToRotation')
    links.new(n_spin.outputs["Vector"], n_e2r.inputs[0])

    # 尾段揭示：reveal = smoothstep(Factor, Reveal Start, Reveal End)
    n_rev = add('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='SMOOTHSTEP')
    links.new(fac, n_rev.inputs["Value"])
    links.new(rv_st,  n_rev.inputs["From Min"])
    links.new(rv_end, n_rev.inputs["From Max"])
    reveal = n_rev.outputs["Result"]

    # 碎块缩放 = (1 - ease*(1-EndScale)) * (1 - reveal) —— 落位收紧 + 尾段缩没
    base_scale = mop('SUBTRACT', av=1.0,
                       b=mop('MULTIPLY', a=ease, b=mop('SUBTRACT', av=1.0, b=endsc)))
    inv_reveal = mop('SUBTRACT', av=1.0, b=reveal)
    shard_scale = mop('MULTIPLY', a=base_scale, b=inv_reveal)

    # 碎块实例化（按索引挑选对应碎块）
    n_coll = add('GeometryNodeCollectionInfo', transform_space='RELATIVE')
    n_coll.inputs["Collection"].default_value = coll
    n_coll.inputs["Separate Children"].default_value = True
    n_coll.inputs["Reset Children"].default_value = True
    n_iop = add('GeometryNodeInstanceOnPoints')
    links.new(n_setpos.outputs["Geometry"], n_iop.inputs["Points"])
    links.new(n_coll.outputs["Instances"], n_iop.inputs["Instance"])
    n_iop.inputs["Pick Instance"].default_value = True
    links.new(n_index.outputs["Index"], n_iop.inputs["Instance Index"])
    links.new(n_e2r.outputs["Rotation"], n_iop.inputs["Rotation"])
    links.new(shard_scale, n_iop.inputs["Scale"])

    # 完整目标模型：在揭示窗口前段快速显现(全尺寸)，碎块缩没后留下完整模型
    n_objinfo = add('GeometryNodeObjectInfo', transform_space='ORIGINAL')
    links.new(n_in.outputs[IN_TARGET], n_objinfo.inputs["Object"])
    # model_in = smoothstep(Factor, Reveal Start, Reveal Start + 0.08) 全尺寸快速登场
    n_min = add('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='SMOOTHSTEP')
    links.new(fac, n_min.inputs["Value"])
    links.new(rv_st, n_min.inputs["From Min"])
    links.new(mop('ADD', a=rv_st, bv=0.08), n_min.inputs["From Max"])
    n_btrans = add('GeometryNodeTransform')
    links.new(n_objinfo.outputs["Geometry"], n_btrans.inputs["Geometry"])
    links.new(n_min.outputs["Result"], n_btrans.inputs["Scale"])  # 浮点广播为等比缩放

    # 合并：飞行碎块 + 完整目标模型
    n_join = add('GeometryNodeJoinGeometry')
    links.new(n_iop.outputs["Instances"], n_join.inputs["Geometry"])
    links.new(n_btrans.outputs["Geometry"], n_join.inputs["Geometry"])
    links.new(n_join.outputs["Geometry"], n_out.inputs["Geometry"])
    return ng


def _socket_id(ng, name):
    """按接口名取 socket 标识符（形如 'Socket_2'）。"""
    for it in ng.interface.items_tree:
        if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.name == name:
            return it.identifier
    raise RuntimeError("找不到输入接口: %s" % name)


def apply_modifier_and_keys(rig, ng, target):
    """挂上几何节点修改器，绑定目标模型，并给 Factor 打关键帧。"""
    mod = rig.modifiers.new("Morph", 'NODES')
    mod.node_group = ng

    # 绑定尾段显现的完整目标模型
    mod[_socket_id(ng, IN_TARGET)] = target

    fac_id = _socket_id(ng, IN_FACTOR)

    def key(frame, val):
        mod[fac_id] = val
        mod.keyframe_insert(data_path='["%s"]' % fac_id, frame=frame)

    key(FRAME_MORPH_A, 0.0)
    key(FRAME_MORPH_B, 1.0)
    key(FRAME_END, 1.0)  # 收尾保持
    return mod


def setup_material(objs):
    """实例化/ObjectInfo 都会继承源网格自身的材质，所以材质要赋给每个源网格。"""
    mat = bpy.data.materials.new("MorphMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.25, 0.12, 1.0)
        if "Metallic" in bsdf.inputs:  bsdf.inputs["Metallic"].default_value = 0.6
        if "Roughness" in bsdf.inputs: bsdf.inputs["Roughness"].default_value = 0.35
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)


def setup_scene_render():
    scn = bpy.context.scene
    scn.frame_start = FRAME_START
    scn.frame_end = FRAME_END
    scn.frame_set(FRAME_START)

    # 相机
    bpy.ops.object.camera_add(location=(0, -7.5, 1.5), rotation=(math.radians(82), 0, 0))
    cam = bpy.context.object
    scn.camera = cam
    # 灯光
    bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
    bpy.context.object.data.energy = 1500
    bpy.context.object.data.size = 5
    # 世界背景
    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)
    # 渲染引擎
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'   # Blender 4.2+/5.x
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'


# ------------------------- 主流程 -------------------------
def main():
    clean_scene()
    src = make_source()
    tgt = make_target()

    pieces, coll = fracture_voronoi(src)
    print("碎块数量:", len(pieces))

    rig = bake_morph_points(pieces, tgt)

    # 目标模型：直接隐藏(只作为表面采样 + 几何节点尾段揭示的数据源)
    # 注意：ObjectInfo 读取的是网格数据，隐藏(eye/render)不影响读取。
    tgt.hide_viewport = True
    tgt.hide_render = True

    # 材质要赋给碎块网格和目标网格(实例/ObjectInfo 都继承源网格材质)
    setup_material(pieces + [tgt])

    ng = build_geo_nodes(coll)
    apply_modifier_and_keys(rig, ng, tgt)
    setup_scene_render()

    print("✅ 完成！按播放查看：球碎块 → 飞散 → 尾段重组为完整猴头模型。")


if __name__ == "__main__":
    main()
