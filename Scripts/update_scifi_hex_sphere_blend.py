import math
from pathlib import Path

import bpy


BLEND_PATH = Path(__file__).resolve().parents[1] / "Content" / "BlenderFile" / "scifi_hex_sphere_with_nodes.blend"


def set_socket_limit(socket, default_value, min_value=None, max_value=None):
    if hasattr(socket, "default_value"):
        socket.default_value = default_value
    if min_value is not None and hasattr(socket, "min_value"):
        socket.min_value = min_value
    if max_value is not None and hasattr(socket, "max_value"):
        socket.max_value = max_value


def clamp_hex_subdivision_controls():
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname != "GeometryNodeTree":
            continue

        for item in node_group.interface.items_tree:
            if (
                getattr(item, "item_type", None) == "SOCKET"
                and getattr(item, "in_out", None) == "INPUT"
                and getattr(item, "name", None) == "Hex Subdivisions"
            ):
                set_socket_limit(item, 2, 1, 2)

        for node in node_group.nodes:
            if node.bl_idname != "GeometryNodeMeshIcoSphere":
                continue
            socket = node.inputs.get("Subdivisions")
            if socket is not None and hasattr(socket, "default_value"):
                socket.default_value = 2


def set_modifier_socket_values():
    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            if modifier.type != "NODES" or modifier.node_group is None:
                continue
            for item in modifier.node_group.interface.items_tree:
                if (
                    getattr(item, "item_type", None) == "SOCKET"
                    and getattr(item, "in_out", None) == "INPUT"
                    and getattr(item, "name", None) == "Hex Subdivisions"
                ):
                    identifier = getattr(item, "identifier", None)
                    if identifier:
                        modifier[identifier] = 2
                        modifier[f"{identifier}_use_attribute"] = False


def tune_outer_shell_modifiers():
    obj = bpy.data.objects.get("Outer_Shell_Hex_Armor_GN")
    if obj is None:
        raise RuntimeError("Outer_Shell_Hex_Armor_GN not found")

    bevel = obj.modifiers.get("Bevel - chamfer plate edges")
    if bevel is not None:
        bevel.segments = 2
        bevel.harden_normals = True

    for polygon in obj.data.polygons:
        polygon.use_smooth = True

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(60.0))
    except Exception:
        weighted = obj.modifiers.get("Weighted Normal - auto smooth")
        if weighted is None:
            weighted = obj.modifiers.new("Weighted Normal - auto smooth", "WEIGHTED_NORMAL")
        weighted.keep_sharp = True
        weighted.weight = 50

    for node_group in bpy.data.node_groups:
        if node_group.bl_idname != "GeometryNodeTree":
            continue
        for node in node_group.nodes:
            if node.bl_idname != "GeometryNodeSetShadeSmooth":
                continue
            shade_socket = node.inputs.get("Shade Smooth")
            if shade_socket is None:
                shade_socket = node.inputs.get("Smooth")
            if shade_socket is not None and hasattr(shade_socket, "default_value"):
                shade_socket.default_value = True


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
    clamp_hex_subdivision_controls()
    set_modifier_socket_values()
    tune_outer_shell_modifiers()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))


if __name__ == "__main__":
    main()
