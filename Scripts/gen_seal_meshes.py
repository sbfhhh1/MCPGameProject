# -*- coding: utf-8 -*-
"""生成中文印章网格：隶书字体 + 布尔 UNION + normals_make_consistent(朝外) + 导出 FBX。
字加大、缩小与边框距离。先用 TEST_CHARS 验证 manifold/法线，确认后再扩到 20 字。
用法: blender --background --python gen_seal_meshes.py
"""
import os
import bmesh
import bpy
from mathutils import Vector

PROJECT_DIR = r"C:\UE_Project\MCPGameProject"
# 关卡文件夹里的隶书字体（方正曹全碑隶书）
FONT_PATH = os.path.join(PROJECT_DIR, "Content", "TransformationVFX", "SM2SM",
                         "font", "FZB070 方正曹全碑隶书", "方正曹全碑隶书.TTF")
OUT_DIR = os.path.join(PROJECT_DIR, "SourceArt", "ChineseSeals")

SECTION_LENGTH = 0.72
HEIGHT_TO_SECTION_RATIO = 2.0
BODY_HEIGHT = SECTION_LENGTH * HEIGHT_TO_SECTION_RATIO
BORDER_HEIGHT = 0.024
BORDER_WIDTH = 0.04
GLYPH_EXTRUDE = 0.028
GLYPH_SIZE = 0.66  # 字加大（原 0.58），缩小与边框的距离

# 随机 20 字测试（自然意象）
TEST_SEALS = [
    ("Shui", "水"), ("Guang", "光"), ("Ying", "影"), ("Feng", "风"),
    ("Yun", "云"), ("Shi", "石"), ("Huo", "火"), ("Shan", "山"),
    ("Hai", "海"), ("Lin", "林"), ("Lei", "雷"), ("Dian", "电"),
    ("Yu", "雨"), ("Xue", "雪"), ("Yue", "月"), ("Ri", "日"),
    ("Xing", "星"), ("Tian", "天"), ("Di", "地"), ("Chuan", "川"),
]


def log(m):
    print("[gen_seal] " + m)


def clean_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def add_cube_box(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def add_rectangular_frame(name):
    outer = SECTION_LENGTH * 0.5
    inner = outer - BORDER_WIDTH
    z0 = BODY_HEIGHT
    z1 = BODY_HEIGHT + BORDER_HEIGHT
    oc = [(-outer, -outer), (outer, -outer), (outer, outer), (-outer, outer)]
    ic = [(-inner, -inner), (inner, -inner), (inner, inner), (-inner, inner)]
    verts = []
    for z in (z0, z1):
        for x, y in oc:
            verts.append((x, y, z))
        for x, y in ic:
            verts.append((x, y, z))
    ob0, ob1, ob2, ob3 = 0, 1, 2, 3
    ib0, ib1, ib2, ib3 = 4, 5, 6, 7
    ot0, ot1, ot2, ot3 = 8, 9, 10, 11
    it0, it1, it2, it3 = 12, 13, 14, 15
    faces = [
        (ot0, ot1, it1, it0), (ot1, ot2, it2, it1), (ot2, ot3, it3, it2), (ot3, ot0, it0, it3),
        (ob1, ob0, ot0, ot1), (ob2, ob1, ot1, ot2), (ob3, ob2, ot2, ot3), (ob0, ob3, ot3, ot0),
        (ib0, ib1, it1, it0), (ib1, ib2, it2, it1), (ib2, ib3, it3, it2), (ib3, ib0, it0, it3),
        (ob0, ib0, ib1, ob1), (ob1, ib1, ib2, ob2), (ob2, ib2, ib3, ob3), (ob3, ib3, ib0, ob0),
    ]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def add_text_mesh(name, body):
    bpy.ops.object.text_add(location=(0.0, 0.0, BODY_HEIGHT + 0.005))
    text = bpy.context.object
    text.name = name
    text.data.body = body
    text.data.align_x = "CENTER"
    text.data.align_y = "CENTER"
    text.data.size = GLYPH_SIZE
    text.data.extrude = GLYPH_EXTRUDE
    text.data.fill_mode = "BOTH"   # 前后都填充实心，不要空心
    text.data.resolution_u = 16
    if os.path.exists(FONT_PATH):
        text.data.font = bpy.data.fonts.load(FONT_PATH)
    else:
        log("WARNING font missing: " + FONT_PATH)
    bpy.ops.object.convert(target="MESH")
    mesh = bpy.context.object
    mesh.name = name
    bpy.context.view_layer.update()
    corners = [mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
    cx = (min(v.x for v in corners) + max(v.x for v in corners)) * 0.5
    cy = (min(v.y for v in corners) + max(v.y for v in corners)) * 0.5
    mesh.location.x -= cx
    mesh.location.y -= cy
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return mesh


def recalc_outside(obj):
    """对单个独立部件重算法线朝外（部件各自是 manifold，结果可靠）。"""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def glyph_finalize(obj):
    """文字网格专用：补洞确保实心，重算法线，再强制顶面 caps 朝上（+Z）、
    底面朝下（-Z），避免隶书复杂笔画的顶面被单面材质剔除而显空心。"""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.fill_holes(sides=0)            # 补所有边界洞（缺失的 caps）
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    # 强制水平面（caps）朝向：顶 +Z、底 -Z
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    zs = [v.co.z for v in bm.verts]
    zmid = (min(zs) + max(zs)) * 0.5
    for f in bm.faces:
        if abs(f.normal.z) > 0.5:  # 近水平面 = caps
            c = f.calc_center_median()
            if c.z > zmid and f.normal.z < 0:
                f.normal_flip()
            elif c.z <= zmid and f.normal.z > 0:
                f.normal_flip()
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()


def join_objects(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.object


def finalize(obj):
    """只居中并应用变换。法线已在各部件 join 前各自重算朝外，这里不再整体重算。"""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0.0, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def collect_mesh_data(obj, name):
    """三角化并导出为 UE 坐标系 .sealmesh 数据：翻Y顶点 + 翻缠绕 + 翻Y法线。
    C++ 端直接使用，不再做坐标/法线处理。"""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    bm.verts.index_update()
    verts = [[round(v.co.x * 100.0, 5), round(-v.co.y * 100.0, 5), round(v.co.z * 100.0, 5)] for v in bm.verts]
    tris = []
    normals = []
    for f in bm.faces:
        vs = list(f.verts)
        if len(vs) != 3:
            continue
        tris.extend([vs[0].index, vs[1].index, vs[2].index])   # 保持 ABC 缠绕（记忆判据 Dot≈-1）
        n = f.normal
        normals.append([round(n.x, 6), round(-n.y, 6), round(n.z, 6)])  # 翻Y法线
    bm.free()
    return {"name": name, "vertices": verts, "triangles": tris, "normals": normals}


def export_fbx(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, apply_unit_scale=True,
        bake_space_transform=False, global_scale=100.0, object_types={"MESH"},
        mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False,
        axis_forward="-Z", axis_up="Y",
    )


def create_seal(token, ch):
    clean_scene()
    cube = add_cube_box("base", (0.0, 0.0, BODY_HEIGHT * 0.5),
                        (SECTION_LENGTH, SECTION_LENGTH, BODY_HEIGHT))
    recalc_outside(cube)
    frame = add_rectangular_frame("frame")
    recalc_outside(frame)
    glyph = add_text_mesh("glyph", ch)
    glyph_finalize(glyph)
    base = join_objects([cube, frame, glyph])
    finalize(base)
    base.name = "SM_Seal_" + token
    base.data.name = base.name
    md = collect_mesh_data(base, base.name)
    log("%s: verts=%d polys=%d sealmesh_tris=%d" %
        (token, len(base.data.vertices), len(base.data.polygons), len(md["triangles"]) // 3))
    return md


def main():
    import json
    os.makedirs(OUT_DIR, exist_ok=True)
    log("font exists: %s" % os.path.exists(FONT_PATH))
    meshes = []
    for token, ch in TEST_SEALS:
        meshes.append(create_seal(token, ch))
    sealmesh_path = os.path.join(OUT_DIR, "chinese_seals_meshes.sealmesh")
    with open(sealmesh_path, "w", encoding="utf-8") as fh:
        json.dump({"meshes": meshes}, fh, ensure_ascii=False)
    clean_scene()
    log("VERTEX_SUMMARY " + json.dumps({m["name"]: len(m["vertices"]) for m in meshes}, ensure_ascii=False))
    log("DONE wrote %d meshes -> chinese_seals_meshes.sealmesh" % len(meshes))


if __name__ == "__main__":
    main()
