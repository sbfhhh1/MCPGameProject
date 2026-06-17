import math
from pathlib import Path

import bpy

BLEND_PATH = Path(r"C:/UE_Project/MCPGameProject/Content/Stool/Stool.blend")
OBJECT_NAME = "Procedural_Stool"
MODIFIER_NAME = "Procedural_Stool_GN"
NODE_GROUP_NAME = "GN_Procedural_Stool_Runtime"


def make_material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def interface_socket(node_group, name, socket_type, default_value, min_value=None, max_value=None):
    socket = node_group.interface.new_socket(name=name, in_out="INPUT", socket_type=socket_type)
    if hasattr(socket, "default_value"):
        socket.default_value = default_value
    if min_value is not None and hasattr(socket, "min_value"):
        socket.min_value = min_value
    if max_value is not None and hasattr(socket, "max_value"):
        socket.max_value = max_value
    return socket


def set_node_vector(node, socket_name, value):
    socket = node.inputs[socket_name]
    try:
        socket.default_value = value
    except TypeError:
        socket.default_value = (value[0], value[1], value[2])


def link_input(group_input, name, target_socket, links):
    links.new(group_input.outputs[name], target_socket)


def add_math(nodes, operation, value=None, location=(0, 0)):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    node.location = location
    if value is not None:
        node.inputs[1].default_value = value
    return node


def add_combine(nodes, location=(0, 0), defaults=None):
    node = nodes.new("ShaderNodeCombineXYZ")
    node.location = location
    if defaults:
        for axis, value in defaults.items():
            node.inputs[axis].default_value = value
    return node


def add_smooth(nodes, links, source, location):
    smooth = nodes.new("GeometryNodeSetShadeSmooth")
    smooth.location = location
    smooth.inputs["Shade Smooth"].default_value = True
    links.new(source, smooth.inputs["Mesh"])
    return smooth


def add_set_material(nodes, links, source, material, location):
    mat_node = nodes.new("GeometryNodeSetMaterial")
    mat_node.location = location
    mat_node.inputs["Material"].default_value = material
    links.new(source, mat_node.inputs["Geometry"])
    return mat_node


def add_cylinder(nodes, links, group_input, name, radius_socket, depth_socket, material, location, vertices_socket=None):
    cylinder = nodes.new("GeometryNodeMeshCylinder")
    cylinder.name = name
    cylinder.location = location
    cylinder.inputs["Vertices"].default_value = 96
    cylinder.inputs["Side Segments"].default_value = 1
    cylinder.inputs["Fill Segments"].default_value = 1
    if vertices_socket:
        link_input(group_input, vertices_socket, cylinder.inputs["Vertices"], links)
    link_input(group_input, radius_socket, cylinder.inputs["Radius"], links)
    link_input(group_input, depth_socket, cylinder.inputs["Depth"], links)
    smooth = add_smooth(nodes, links, cylinder.outputs["Mesh"], (location[0] + 210, location[1]))
    mat_node = add_set_material(nodes, links, smooth.outputs["Mesh"], material, (location[0] + 420, location[1]))
    return mat_node


def add_curve_tube(nodes, links, start_socket, end_socket, radius_source, material, location, name):
    curve = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    curve.name = f"{name}_Segment"
    curve.location = location
    curve.inputs["Resolution"].default_value = 8
    links.new(start_socket, curve.inputs["Start"])
    links.new(start_socket, curve.inputs["Start Handle"])
    links.new(end_socket, curve.inputs["End Handle"])
    links.new(end_socket, curve.inputs["End"])

    profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    profile.name = f"{name}_Profile"
    profile.location = (location[0], location[1] - 135)
    profile.inputs["Resolution"].default_value = 24
    links.new(radius_source, profile.inputs["Radius"])

    tube = nodes.new("GeometryNodeCurveToMesh")
    tube.name = f"{name}_Tube"
    tube.location = (location[0] + 250, location[1])
    tube.inputs["Fill Caps"].default_value = True
    links.new(curve.outputs["Curve"], tube.inputs["Curve"])
    links.new(profile.outputs["Curve"], tube.inputs["Profile Curve"])

    smooth = add_smooth(nodes, links, tube.outputs["Mesh"], (location[0] + 470, location[1]))
    return add_set_material(nodes, links, smooth.outputs["Mesh"], material, (location[0] + 690, location[1]))


def build_tree(node_group, rubber_mat, wood_mat, metal_mat):
    node_group.nodes.clear()
    node_group.interface.clear()
    node_group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    interface_socket(node_group, "Seat Radius", "NodeSocketFloat", 0.445, 0.32, 0.62)
    interface_socket(node_group, "Seat Thickness", "NodeSocketFloat", 0.082, 0.045, 0.16)
    interface_socket(node_group, "Leg Height", "NodeSocketFloat", 1.05, 0.78, 1.32)
    interface_socket(node_group, "Leg Radius", "NodeSocketFloat", 0.022, 0.012, 0.045)
    interface_socket(node_group, "Leg Spread", "NodeSocketFloat", 0.355, 0.24, 0.52)
    interface_socket(node_group, "Leg Segments", "NodeSocketInt", 28, 12, 48)
    interface_socket(node_group, "Brace Height", "NodeSocketFloat", 0.42, 0.24, 0.66)
    interface_socket(node_group, "Foot Pad Scale", "NodeSocketFloat", 0.62, 0.25, 1.0)

    nodes = node_group.nodes
    links = node_group.links
    group_input = nodes.new("NodeGroupInput")
    group_input.location = (-1450, 120)
    group_input.name = "Exposed Stool Controls"
    group_output = nodes.new("NodeGroupOutput")
    group_output.location = (1180, 120)

    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (930, 120)
    links.new(join.outputs["Geometry"], group_output.inputs["Geometry"])

    seat = add_cylinder(
        nodes,
        links,
        group_input,
        "Round_Wood_Seat",
        "Seat Radius",
        "Seat Thickness",
        wood_mat,
        (-1160, 580),
    )
    links.new(seat.outputs["Geometry"], join.inputs["Geometry"])

    leg_z = add_math(nodes, "MULTIPLY", -0.5, (-1200, 285))
    links.new(group_input.outputs["Leg Height"], leg_z.inputs[0])
    brace_z = add_math(nodes, "MULTIPLY", -1.0, (-1200, 125))
    links.new(group_input.outputs["Brace Height"], brace_z.inputs[0])
    foot_z = add_math(nodes, "MULTIPLY", -1.0, (-1200, -35))
    links.new(group_input.outputs["Leg Height"], foot_z.inputs[0])
    top_spread_math = add_math(nodes, "MULTIPLY", 0.47, (-1200, -195))
    links.new(group_input.outputs["Leg Spread"], top_spread_math.inputs[0])

    foot_scale = add_math(nodes, "MULTIPLY_ADD", None, (-1200, -355))
    foot_scale.inputs[1].default_value = 1.65
    foot_scale.inputs[2].default_value = 1.15
    links.new(group_input.outputs["Foot Pad Scale"], foot_scale.inputs[0])
    foot_radius = add_math(nodes, "MULTIPLY", None, (-960, -355))
    links.new(group_input.outputs["Leg Radius"], foot_radius.inputs[0])
    links.new(foot_scale.outputs[0], foot_radius.inputs[1])

    ring_radius = add_math(nodes, "MULTIPLY", 1.12, (-1200, -520))
    links.new(group_input.outputs["Leg Spread"], ring_radius.inputs[0])
    ring_tube_radius = add_math(nodes, "MULTIPLY", 0.86, (-1200, -640))
    links.new(group_input.outputs["Leg Radius"], ring_tube_radius.inputs[0])

    leg_specs = [
        ("Front_Right", 1.0, 1.0, -720),
        ("Back_Right", -1.0, 1.0, -1030),
        ("Back_Left", -1.0, -1.0, -1340),
        ("Front_Left", 1.0, -1.0, -1650),
    ]

    for label, sx, sy, y in leg_specs:
        top_x = add_math(nodes, "MULTIPLY", sx * 0.47, (-1010, y + 105))
        top_y = add_math(nodes, "MULTIPLY", sy * 0.47, (-1010, y + 55))
        foot_x = add_math(nodes, "MULTIPLY", sx, (-1010, y - 15))
        foot_y = add_math(nodes, "MULTIPLY", sy, (-1010, y - 65))
        ring_x = add_math(nodes, "MULTIPLY", sx * 1.03, (-1010, y - 135))
        ring_y = add_math(nodes, "MULTIPLY", sy * 1.03, (-1010, y - 185))
        links.new(group_input.outputs["Leg Spread"], top_x.inputs[0])
        links.new(group_input.outputs["Leg Spread"], top_y.inputs[0])
        links.new(group_input.outputs["Leg Spread"], foot_x.inputs[0])
        links.new(group_input.outputs["Leg Spread"], foot_y.inputs[0])
        links.new(group_input.outputs["Leg Spread"], ring_x.inputs[0])
        links.new(group_input.outputs["Leg Spread"], ring_y.inputs[0])

        top = add_combine(nodes, (-735, y + 70))
        links.new(top_x.outputs[0], top.inputs["X"])
        links.new(top_y.outputs[0], top.inputs["Y"])
        top.inputs["Z"].default_value = -0.02

        foot = add_combine(nodes, (-735, y - 60))
        links.new(foot_x.outputs[0], foot.inputs["X"])
        links.new(foot_y.outputs[0], foot.inputs["Y"])
        links.new(foot_z.outputs[0], foot.inputs["Z"])

        leg = add_curve_tube(
            nodes,
            links,
            top.outputs["Vector"],
            foot.outputs["Vector"],
            group_input.outputs["Leg Radius"],
            metal_mat,
            (-500, y + 35),
            f"{label}_Angled_Metal_Leg",
        )
        links.new(leg.outputs["Geometry"], join.inputs["Geometry"])

        ring_point = add_combine(nodes, (-735, y - 210))
        links.new(ring_x.outputs[0], ring_point.inputs["X"])
        links.new(ring_y.outputs[0], ring_point.inputs["Y"])
        links.new(brace_z.outputs[0], ring_point.inputs["Z"])
        upright = add_curve_tube(
            nodes,
            links,
            ring_point.outputs["Vector"],
            foot.outputs["Vector"],
            ring_tube_radius.outputs[0],
            metal_mat,
            (-500, y - 260),
            f"{label}_Lower_Metal_Strut",
        )
        links.new(upright.outputs["Geometry"], join.inputs["Geometry"])

        foot_pad = nodes.new("GeometryNodeMeshCylinder")
        foot_pad.name = f"{label}_Black_Rubber_Foot"
        foot_pad.location = (-500, y - 520)
        foot_pad.inputs["Vertices"].default_value = 32
        foot_pad.inputs["Depth"].default_value = 0.052
        links.new(foot_radius.outputs[0], foot_pad.inputs["Radius"])
        links.new(group_input.outputs["Leg Segments"], foot_pad.inputs["Vertices"])

        foot_transform = nodes.new("GeometryNodeTransform")
        foot_transform.location = (-250, y - 520)
        links.new(foot_pad.outputs["Mesh"], foot_transform.inputs["Geometry"])
        links.new(foot.outputs["Vector"], foot_transform.inputs["Translation"])

        foot_smooth = add_smooth(nodes, links, foot_transform.outputs["Geometry"], (-20, y - 520))
        foot_mat = add_set_material(nodes, links, foot_smooth.outputs["Mesh"], rubber_mat, (220, y - 520))
        links.new(foot_mat.outputs["Geometry"], join.inputs["Geometry"])

    ring_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    ring_circle.name = "Circular_Metal_Foot_Ring"
    ring_circle.location = (-500, -2060)
    ring_circle.inputs["Resolution"].default_value = 96
    links.new(ring_radius.outputs[0], ring_circle.inputs["Radius"])

    ring_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    ring_profile.name = "Foot_Ring_Tube_Profile"
    ring_profile.location = (-500, -2200)
    ring_profile.inputs["Resolution"].default_value = 18
    links.new(ring_tube_radius.outputs[0], ring_profile.inputs["Radius"])

    ring_mesh = nodes.new("GeometryNodeCurveToMesh")
    ring_mesh.location = (-250, -2060)
    ring_mesh.inputs["Fill Caps"].default_value = True
    links.new(ring_circle.outputs["Curve"], ring_mesh.inputs["Curve"])
    links.new(ring_profile.outputs["Curve"], ring_mesh.inputs["Profile Curve"])

    ring_loc = add_combine(nodes, (-250, -2230))
    links.new(brace_z.outputs[0], ring_loc.inputs["Z"])
    ring_transform = nodes.new("GeometryNodeTransform")
    ring_transform.location = (0, -2060)
    links.new(ring_mesh.outputs["Mesh"], ring_transform.inputs["Geometry"])
    links.new(ring_loc.outputs["Vector"], ring_transform.inputs["Translation"])
    ring_smooth = add_smooth(nodes, links, ring_transform.outputs["Geometry"], (220, -2060))
    ring_mat = add_set_material(nodes, links, ring_smooth.outputs["Mesh"], metal_mat, (450, -2060))
    links.new(ring_mat.outputs["Geometry"], join.inputs["Geometry"])


def remove_old_runtime_objects():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Procedural_Stool") or obj.name == "Cube":
            bpy.data.objects.remove(obj, do_unlink=True)


def ensure_host():
    mesh = bpy.data.meshes.new(OBJECT_NAME + "_HostMesh")
    obj = bpy.data.objects.new(OBJECT_NAME, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, math.radians(8.0))
    obj.scale = (1.0, 1.0, 1.0)
    return obj


def main():
    if BLEND_PATH.exists():
        bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

    remove_old_runtime_objects()
    rubber_mat = make_material("GN_Dark_Grey_Rubber.002", (0.015, 0.015, 0.018, 1.0), 0.0, 0.72)
    wood_mat = make_material("GN_Seat_Wood.002", (0.64, 0.34, 0.15, 1.0), 0.0, 0.34)
    metal_mat = make_material("GN_Light_Grey_Metal.002", (0.68, 0.70, 0.72, 1.0), 0.75, 0.22)

    obj = ensure_host()
    obj.data.materials.clear()
    obj.data.materials.append(rubber_mat)
    obj.data.materials.append(wood_mat)
    obj.data.materials.append(metal_mat)

    node_group = bpy.data.node_groups.get(NODE_GROUP_NAME)
    if not node_group:
        node_group = bpy.data.node_groups.new(NODE_GROUP_NAME, "GeometryNodeTree")
    build_tree(node_group, rubber_mat, wood_mat, metal_mat)

    modifier = obj.modifiers.new(MODIFIER_NAME, "NODES")
    modifier.node_group = node_group

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(f"Patched {BLEND_PATH} with a real Geometry Nodes stool graph.")


if __name__ == "__main__":
    main()
