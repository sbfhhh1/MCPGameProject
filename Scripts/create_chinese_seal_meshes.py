# -*- coding: utf-8 -*-
"""Create Chinese seal meshes in Blender and export runtime mesh data for UE."""

import json
import os

import bpy
from mathutils import Vector

PROJECT_DIR = r"C:\UE_Project\MCPGameProject"
FONT_PATH = os.path.join(
    PROJECT_DIR,
    "Content",
    "TransformationVFX",
    "SM2SM",
    "font",
    "FZB070 \u65b9\u6b63\u66f9\u5168\u7891\u96b6\u4e66",
    "\u65b9\u6b63\u66f9\u5168\u7891\u96b6\u4e66.TTF",
)
OUT_DIR = os.path.join(PROJECT_DIR, "SourceArt", "ChineseSeals")
MESH_DATA_PATH = os.path.join(OUT_DIR, "chinese_seals_meshes.sealmesh")

SECTION_LENGTH = 0.72
HEIGHT_TO_SECTION_RATIO = 2.0
BODY_HEIGHT = SECTION_LENGTH * HEIGHT_TO_SECTION_RATIO
BORDER_HEIGHT = 0.024
BORDER_WIDTH = 0.04
GLYPH_EXTRUDE = 0.028

SEALS = [
    ("Chuan", "\u5ddd"),
    ("Di", "\u5730"),
    ("Dian", "\u7535"),
    ("Feng", "\u98ce"),
    ("Guang", "\u5149"),
    ("Hai", "\u6d77"),
    ("Huo", "\u706b"),
    ("Lei", "\u96f7"),
    ("Lin", "\u6797"),
    ("Ri", "\u65e5"),
    ("Shan", "\u5c71"),
    ("Shi", "\u77f3"),
    ("Shui", "\u6c34"),
    ("Tian", "\u5929"),
    ("Xing", "\u661f"),
    ("Xue", "\u96ea"),
    ("Ying", "\u5f71"),
    ("Yu", "\u96e8"),
    ("Yue", "\u6708"),
    ("Yun", "\u4e91"),
]


def clean_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name, color, roughness=0.5, metallic=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Alpha"].default_value = alpha
    return mat


def add_cube_box(name, location, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.data.materials.append(mat)
    return obj


def add_body_with_frame(name, material):
    outer = SECTION_LENGTH * 0.5
    inner = outer - BORDER_WIDTH
    base_z = 0.0
    deck_z = BODY_HEIGHT
    frame_z = BODY_HEIGHT + BORDER_HEIGHT

    outer_corners = [
        (-outer, -outer),
        (outer, -outer),
        (outer, outer),
        (-outer, outer),
    ]
    inner_corners = [
        (-inner, -inner),
        (inner, -inner),
        (inner, inner),
        (-inner, inner),
    ]

    verts = []
    for z in (base_z, deck_z, frame_z):
        for x, y in outer_corners:
            verts.append((x, y, z))
        for x, y in inner_corners:
            verts.append((x, y, z))

    ob0, ob1, ob2, ob3 = 0, 1, 2, 3
    db0, db1, db2, db3 = 4, 5, 6, 7
    od0, od1, od2, od3 = 8, 9, 10, 11
    id0, id1, id2, id3 = 12, 13, 14, 15
    of0, of1, of2, of3 = 16, 17, 18, 19
    if0, if1, if2, if3 = 20, 21, 22, 23

    faces = [
        (ob3, ob2, ob1, ob0),
        (ob0, ob1, od1, od0),
        (ob1, ob2, od2, od1),
        (ob2, ob3, od3, od2),
        (ob3, ob0, od0, od3),
        (id0, id1, id2, id3),
        (od0, od1, id1, id0),
        (od1, od2, id2, id1),
        (od2, od3, id3, id2),
        (od3, od0, id0, id3),
        (of0, if0, if1, of1),
        (of1, if1, if2, of2),
        (of2, if2, if3, of3),
        (of3, if3, if0, of0),
        (od0, of0, of1, od1),
        (od1, of1, of2, od2),
        (od2, of2, of3, od3),
        (od3, of3, of0, od0),
        (id1, if1, if0, id0),
        (id2, if2, if1, id1),
        (id3, if3, if2, id2),
        (id0, if0, if3, id3),
    ]

    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def add_text_mesh(name, body, material):
    bpy.ops.object.text_add(location=(0.0, 0.0, BODY_HEIGHT + BORDER_HEIGHT), rotation=(0.0, 0.0, 0.0))
    text = bpy.context.object
    text.name = name
    text.data.body = body
    text.data.align_x = "CENTER"
    text.data.align_y = "CENTER"
    text.data.size = 0.58
    text.data.extrude = GLYPH_EXTRUDE
    text.data.resolution_u = 18
    text.data.bevel_depth = 0.0
    text.data.bevel_resolution = 0
    if os.path.exists(FONT_PATH):
        text.data.font = bpy.data.fonts.load(FONT_PATH)

    bpy.ops.object.convert(target="MESH")
    mesh = bpy.context.object
    mesh.name = name
    mesh.data.materials.append(material)

    bpy.context.view_layer.update()
    corners = [mesh.matrix_world @ Vector(corner) for corner in mesh.bound_box]
    cx = (min(v.x for v in corners) + max(v.x for v in corners)) * 0.5
    cy = (min(v.y for v in corners) + max(v.y for v in corners)) * 0.5
    mesh.location.x -= cx
    mesh.location.y -= cy

    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return mesh


def collect_mesh_data(obj, token):
    tri = obj.modifiers.new("triangulate_for_runtime", "TRIANGULATE")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=tri.name)
    mesh = obj.data
    mesh.update(calc_edges=True)

    zmax = max((vertex.co.z for vertex in mesh.vertices), default=0.0)
    for poly in mesh.polygons:
        center_z = sum(mesh.vertices[index].co.z for index in poly.vertices) / max(len(poly.vertices), 1)
        if center_z > zmax - 0.01 and poly.normal.z < 0.0:
            poly.flip()
    mesh.update(calc_edges=True)

    vertices = []
    for vertex in mesh.vertices:
        co = vertex.co
        vertices.append([round(co.x * 100.0, 5), round(co.y * 100.0, 5), round(co.z * 100.0, 5)])

    triangles = []
    normals = []
    uvs = []
    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
    for poly in mesh.polygons:
        if len(poly.vertices) == 3:
            triangles.extend([int(poly.vertices[0]), int(poly.vertices[1]), int(poly.vertices[2])])
            normal = poly.normal
            normals.append([round(normal.x, 6), round(normal.y, 6), round(normal.z, 6)])
            for loop_index in poly.loop_indices:
                if uv_layer:
                    uv = uv_layer[loop_index].uv
                    uvs.append([round(uv.x, 6), round(uv.y, 6)])
                else:
                    uvs.append([0.0, 0.0])

    return {
        "name": token,
        "section_length_cm": round(SECTION_LENGTH * 100.0, 5),
        "height_to_section_ratio": HEIGHT_TO_SECTION_RATIO,
        "vertices": vertices,
        "triangles": triangles,
        "normals": normals,
        "uvs": uvs,
    }


def join_and_export(objects, export_path, token):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.location = (0.0, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    joined.name = os.path.splitext(os.path.basename(export_path))[0]
    joined.data.name = joined.name

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_flat()

    mesh_data = collect_mesh_data(joined, token)

    bpy.ops.object.select_all(action="DESELECT")
    joined.select_set(True)
    bpy.context.view_layer.objects.active = joined
    bpy.ops.export_scene.fbx(
        filepath=export_path,
        use_selection=True,
        apply_unit_scale=True,
        bake_space_transform=False,
        global_scale=100.0,
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        axis_forward="-Z",
        axis_up="Y",
    )
    return mesh_data


def create_seal(token, character):
    clean_scene()
    white_pbr = make_material("M_Seal_DefaultWhitePBR", (1.0, 1.0, 1.0, 1.0), 0.5, 0.0, 1.0)

    objects = [
        add_body_with_frame("seal_body_frame", white_pbr)
    ]

    objects.append(add_text_mesh("glyph_" + token, character, white_pbr))

    export_path = os.path.join(OUT_DIR, "SM_Seal_{}.fbx".format(token))
    return join_and_export(objects, export_path, token)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    meshes = []
    for token, character in SEALS:
        meshes.append(create_seal(token, character))
    with open(MESH_DATA_PATH, "w", encoding="utf-8") as fh:
        json.dump({"meshes": meshes}, fh, ensure_ascii=False)
    clean_scene()


if __name__ == "__main__":
    main()
