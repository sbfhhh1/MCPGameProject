import json
import struct
import sys
from array import array
from pathlib import Path

import bpy
import bmesh


def log(message):
    print("[OpenClawGN] " + message, flush=True)


def load_request():
    if "--" not in sys.argv:
        raise RuntimeError("Missing request json path after --")

    request_path = Path(sys.argv[sys.argv.index("--") + 1])
    with request_path.open("r", encoding="utf-8-sig") as handle:
        request = json.load(handle)

    if not request.get("outputPath"):
        raise RuntimeError("Request is missing required outputPath")
    return request


def find_modifier(obj, modifier_name):
    if modifier_name:
        modifier = obj.modifiers.get(modifier_name)
        if modifier is not None:
            if modifier.type != "NODES":
                raise RuntimeError(f"Modifier '{modifier_name}' on object '{obj.name}' is not a Geometry Nodes modifier")
            return modifier

    for modifier in obj.modifiers:
        if modifier.type == "NODES":
            return modifier

    raise RuntimeError(f"No Geometry Nodes modifier found on object '{obj.name}'")


def interface_identifier_by_name(node_group, socket_name):
    if not node_group or not socket_name:
        return None

    for item in node_group.interface.items_tree:
        if (
            getattr(item, "item_type", None) == "SOCKET"
            and getattr(item, "in_out", None) == "INPUT"
            and getattr(item, "name", None) == socket_name
        ):
            return getattr(item, "identifier", None)

    return None


def group_input_socket_identifier_by_name(node_group, socket_name):
    if not node_group or not socket_name:
        return None

    for node in node_group.nodes:
        if node.bl_idname != "NodeGroupInput":
            continue
        for output in node.outputs:
            if output.name == socket_name:
                return getattr(output, "identifier", None)

    return None


def node_group_input_sockets_by_name(node_group, socket_name):
    if not node_group or not socket_name:
        return []

    sockets = []
    for node in node_group.nodes:
        if node.bl_idname != "NodeGroupInput":
            continue
        for output in node.outputs:
            if output.name == socket_name:
                sockets.append(output)
    return sockets


def set_modifier_input(modifier, node_group, item):
    socket_name = item.get("name", "")
    fallback = item.get("fallbackIdentifier", "")
    explicit_identifier = item.get("identifier", "")
    value = item.get("value")
    existing_keys = set(modifier.keys())

    candidates = [
        fallback,
        explicit_identifier,
        interface_identifier_by_name(node_group, socket_name),
        group_input_socket_identifier_by_name(node_group, socket_name),
        socket_name,
    ]

    seen = set()
    for key in candidates:
        if not key or key in seen:
            continue
        seen.add(key)
        if key not in existing_keys:
            continue
        try:
            modifier[key] = value
            log(f"Set {socket_name or key} via modifier key {key} = {value}")
            return True
        except Exception as exc:
            log(f"Warning: failed setting modifier key '{key}' for '{socket_name}': {exc}")

    log(f"Warning: could not set GN input '{socket_name}' on modifier '{modifier.name}'")
    return False


def remove_links_to_socket(node_group, socket):
    for link in list(node_group.links):
        if link.to_socket == socket:
            node_group.links.remove(link)


def set_socket_default_value(socket, value):
    if not hasattr(socket, "default_value"):
        return False

    current = socket.default_value
    try:
        if hasattr(current, "__len__") and not isinstance(current, (str, bytes)):
            if isinstance(value, (list, tuple)):
                for index in range(min(len(current), len(value))):
                    current[index] = float(value[index])
            else:
                scalar = float(value)
                for index in range(len(current)):
                    current[index] = scalar
        elif isinstance(current, bool):
            socket.default_value = bool(value)
        elif isinstance(current, int):
            socket.default_value = int(value)
        else:
            socket.default_value = float(value)
        return True
    except Exception:
        try:
            socket.default_value = value
            return True
        except Exception:
            return False


def try_apply_linked_group_input_override(node_group, item):
    socket_name = item.get("name", "")
    if not node_group or not socket_name:
        return False

    changed = False
    for output in node_group_input_sockets_by_name(node_group, socket_name):
        for link in list(output.links):
            target_socket = link.to_socket
            if set_socket_default_value(target_socket, item.get("value")):
                node_group.links.remove(link)
                changed = True

    if changed:
        log(f"Set {socket_name} by overriding linked node sockets = {item.get('value')}")
    return changed


def try_apply_builtin_node_override(node_group, item):
    socket_name = item.get("name", "")
    if socket_name == "Goo Contrast":
        value = max(0.0, min(1.0, float(item.get("value", 0.35))))
        center = 0.48
        half_width = 0.48 - value * 0.26
        changed = False
        for node in node_group.nodes:
            if node.name != "Noise Contrast ColorRamp" or not hasattr(node, "color_ramp"):
                continue
            ramp = node.color_ramp
            if len(ramp.elements) >= 2:
                ramp.elements[0].position = max(0.0, center - half_width)
                ramp.elements[1].position = min(1.0, center + half_width)
                changed = True
        if changed:
            log(f"Set Goo Contrast by widening Noise Contrast ColorRamp = {value}")
        return changed

    if socket_name != "Hex Subdivisions":
        return False

    value = int(item.get("value", 3))
    value = max(1, min(3, value))
    changed = False
    for node in node_group.nodes:
        if node.bl_idname != "GeometryNodeMeshIcoSphere":
            continue
        socket = node.inputs.get("Subdivisions")
        if socket is None:
            continue
        remove_links_to_socket(node_group, socket)
        socket.default_value = value
        changed = True

    if changed:
        log(f"Set Hex Subdivisions by overriding Ico Sphere node sockets = {value}")
    return changed


def write_numeric_array(handle, typecode, values):
    if not values:
        return

    packed = array(typecode, values)
    if sys.byteorder != "little":
        packed.byteswap()
    packed.tofile(handle)


def write_binary_mesh_cache(output_path, object_name, vertices, normals, uvs, triangles, material_indices, material_names):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        handle.write(b"OCGNMESH")
        handle.write(struct.pack("<I", 2))
        encoded_name = object_name.encode("utf-8")
        handle.write(struct.pack("<I", len(encoded_name)))
        handle.write(encoded_name)
        handle.write(struct.pack("<IIIII", len(vertices), len(normals), len(uvs), len(triangles), len(material_indices)))
        write_numeric_array(handle, "f", vertices)
        write_numeric_array(handle, "f", normals)
        write_numeric_array(handle, "f", uvs)
        write_numeric_array(handle, "i", triangles)
        write_numeric_array(handle, "i", material_indices)
        handle.write(struct.pack("<I", len(material_names)))
        for material_name in material_names:
            encoded = material_name.encode("utf-8")
            handle.write(struct.pack("<I", len(encoded)))
            handle.write(encoded)


def socket_float(node, name, fallback):
    socket = node.inputs.get(name) if node else None
    if socket is not None and hasattr(socket, "default_value"):
        try:
            return float(socket.default_value)
        except Exception:
            return fallback
    return fallback


def socket_color(node, name, fallback):
    socket = node.inputs.get(name) if node else None
    if socket is not None and hasattr(socket, "default_value"):
        value = socket.default_value
        try:
            if hasattr(value, "__len__") and len(value) >= 3:
                alpha = float(value[3]) if len(value) > 3 else fallback[3]
                return [float(value[0]), float(value[1]), float(value[2]), alpha]
        except Exception:
            return fallback
    return fallback


def find_principled_bsdf(material):
    if not material or not material.use_nodes or not material.node_tree:
        return None

    for node in material.node_tree.nodes:
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            return node
    return None


def material_metadata(mesh):
    names = []
    colors = []
    metallic = []
    roughness = []
    for material in mesh.materials:
        names.append(material.name if material else "")
        color = [0.72, 0.72, 0.68, 1.0]
        diffuse = getattr(material, "diffuse_color", None) if material else None
        if diffuse is not None:
            color = [float(diffuse[0]), float(diffuse[1]), float(diffuse[2]), float(diffuse[3])]

        principled = find_principled_bsdf(material)
        if principled:
            color = socket_color(principled, "Base Color", color)
        colors.extend(color)
        metallic.append(socket_float(principled, "Metallic", 0.0))
        roughness.append(socket_float(principled, "Roughness", 0.45))
    return names, colors, metallic, roughness


def write_json_mesh_cache(
    output_path,
    object_name,
    vertices,
    normals,
    uvs,
    triangles,
    material_indices,
    material_names,
    material_colors,
    material_metallic,
    material_roughness,
):
    data = {
        "objectName": object_name,
        "vertices": vertices,
        "normals": normals,
        "uvs": uvs,
        "triangles": triangles,
        "materialIndices": material_indices,
        "materialNames": material_names,
        "materialBaseColors": material_colors,
        "materialMetallic": material_metallic,
        "materialRoughness": material_roughness,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, separators=(",", ":"))


def cube_project_uv(co, normal, bounds_min, bounds_size):
    ax = abs(normal.x)
    ay = abs(normal.y)
    az = abs(normal.z)
    sx = bounds_size.x if bounds_size.x > 1.0e-6 else 1.0
    sy = bounds_size.y if bounds_size.y > 1.0e-6 else 1.0
    sz = bounds_size.z if bounds_size.z > 1.0e-6 else 1.0
    if ax >= ay and ax >= az:
        return ((co.z - bounds_min.z) / sz, (co.y - bounds_min.y) / sy)
    if ay >= ax and ay >= az:
        return ((co.x - bounds_min.x) / sx, (co.z - bounds_min.z) / sz)
    return ((co.x - bounds_min.x) / sx, (co.y - bounds_min.y) / sy)


def mesh_bounds(mesh):
    if not mesh.vertices:
        return None, None

    bounds_min = mesh.vertices[0].co.copy()
    bounds_max = mesh.vertices[0].co.copy()
    for vertex in mesh.vertices:
        bounds_min.x = min(bounds_min.x, vertex.co.x)
        bounds_min.y = min(bounds_min.y, vertex.co.y)
        bounds_min.z = min(bounds_min.z, vertex.co.z)
        bounds_max.x = max(bounds_max.x, vertex.co.x)
        bounds_max.y = max(bounds_max.y, vertex.co.y)
        bounds_max.z = max(bounds_max.z, vertex.co.z)

    return bounds_min, bounds_max - bounds_min


def loop_uv(mesh, loop_index, co, normal, bounds_min, bounds_size):
    if mesh.uv_layers.active and loop_index < len(mesh.uv_layers.active.data):
        uv = mesh.uv_layers.active.data[loop_index].uv
        return (float(uv.x), float(uv.y))
    if bounds_min is not None:
        return cube_project_uv(co, normal, bounds_min, bounds_size)
    return (0.0, 0.0)


def repair_evaluated_mesh_normals(mesh):
    """Apply a Blender-side normal fix before serializing for Unreal."""
    if not mesh or not mesh.polygons:
        return

    try:
        mesh.validate(clean_customdata=False)
    except Exception as exc:
        log(f"Warning: mesh validation before normal repair failed: {exc}")

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.normal_update()
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
    finally:
        bm.free()

    # Custom split normals from a GN graph can keep stale or inverted loop normals.
    # Zero custom loop normals asks Blender to use the repaired face/loop normals.
    if hasattr(mesh, "normals_split_custom_set") and mesh.loops:
        try:
            mesh.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(mesh.loops))
        except Exception as exc:
            log(f"Warning: clearing custom split normals failed: {exc}")

    mesh.update(calc_edges=True)
    mesh.calc_loop_triangles()


def evaluated_mesh_to_cache(obj, output_path, mesh_format):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        repair_evaluated_mesh_normals(mesh)
        vertices = []
        normals = []
        uvs = []
        bounds_min, bounds_size = mesh_bounds(mesh)
        triangles = []
        material_indices = []
        next_index = 0
        for tri in mesh.loop_triangles:
            for loop_index, vertex_index in zip(tri.loops, tri.vertices):
                vertex = mesh.vertices[vertex_index]
                loop = mesh.loops[loop_index]
                co = vertex.co
                no = loop.normal
                vertices.extend([co.x, co.y, co.z])
                normals.extend([no.x, no.y, no.z])
                uv = loop_uv(mesh, loop_index, co, no, bounds_min, bounds_size)
                uvs.extend([uv[0], uv[1]])
                triangles.append(next_index)
                next_index += 1
            material_indices.append(tri.material_index)

        material_names, material_colors, material_metallic, material_roughness = material_metadata(mesh)

        if mesh_format == "binary":
            write_binary_mesh_cache(output_path, obj.name, vertices, normals, uvs, triangles, material_indices, material_names)
        else:
            write_json_mesh_cache(
                output_path,
                obj.name,
                vertices,
                normals,
                uvs,
                triangles,
                material_indices,
                material_names,
                material_colors,
                material_metallic,
                material_roughness,
            )
        log(f"Exported {len(vertices) // 3} split vertices, {len(mesh.loop_triangles)} triangles to {output_path}")
    finally:
        evaluated.to_mesh_clear()


def apply_inputs(modifier, node_group, inputs):
    for item in inputs:
        if not isinstance(item, dict):
            log(f"Warning: skipped malformed input item {item}")
            continue

        if not try_apply_builtin_node_override(node_group, item):
            if not try_apply_linked_group_input_override(node_group, item):
                set_modifier_input(modifier, node_group, item)


def set_scene_frame(request):
    frame_rate = float(request.get("frameRate", bpy.context.scene.render.fps))
    unity_time = float(request.get("unityTime", max(0.0, bpy.context.scene.frame_current / max(1.0, frame_rate))))
    bpy.context.scene.render.fps = max(1, int(round(frame_rate)))
    frame = int(request.get("frame", 1 + round(unity_time * frame_rate)))
    bpy.context.scene.frame_set(max(1, frame))
    log(f"Animation time = {unity_time:.3f}s, frame = {max(1, frame)}, fps = {bpy.context.scene.render.fps}")


def main():
    request = load_request()
    object_name = request.get("objectName", "")
    obj = bpy.data.objects.get(object_name)
    if obj is None:
        available = ", ".join(sorted(bpy.data.objects.keys()))
        raise RuntimeError(f"Object '{object_name}' not found. Available objects: {available}")

    modifier = find_modifier(obj, request.get("modifierName", ""))
    node_group = modifier.node_group
    if node_group is None:
        raise RuntimeError(f"Geometry Nodes modifier '{modifier.name}' has no node group")

    apply_inputs(modifier, node_group, request.get("inputs", []))

    obj.update_tag()
    modifier.id_data.update_tag()
    node_group.update_tag()
    set_scene_frame(request)
    bpy.context.view_layer.update()
    evaluated_mesh_to_cache(obj, request["outputPath"], request.get("meshFormat", "json"))


if __name__ == "__main__":
    main()
