"""Produce and re-import uncompressed GLB and Blender assets from native CAD triangulation."""
import json
import math
import sys
from collections import Counter
from itertools import product
from pathlib import Path

import bpy

BASE = Path(__file__).resolve().parents[2]
SPEC = json.loads((BASE / "cad/stage4b/west-gate-left/spec.json").read_text())
DEFS = SPEC["definitions"]
ROWS = SPEC["instances"]
BLENDS = BASE / "blender/stage4b"
CAD = BASE / "cad/stage4b/west-gate-left"


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    units = bpy.context.scene.unit_settings
    units.system, units.scale_length = "METRIC", 1.0


def inspect(expected):
    objs = {o.name: o for o in bpy.context.scene.objects}
    if objs.keys() != expected.keys():
        raise ValueError(f"unexpected object set: {list(objs)}")
    tol = 2e-6
    for name, (lo_mm, sz_mm) in expected.items():
        obj = objs[name]
        obj.data.calc_loop_triangles()
        extents = [[lo_mm[i]/1000,(lo_mm[i]+sz_mm[i])/1000] for i in range(3)]
        verts = {}
        for v in obj.data.vertices:
            point = obj.matrix_world @ v.co
            flags = tuple(min((0,1),key=lambda i: abs(x-d[i])) for x,d in zip(point, extents))
            if any(not math.isfinite(x) or abs(x-d[i]) > tol for x,d,i in zip(point,extents,flags)):
                raise ValueError(f"unexpected ({name}) vertex {point}")
            verts[v.index] = flags
        if set(verts.values()) != set(product((0,1),repeat=3)):
            raise ValueError("missing corner")
        planes, edges = Counter(), Counter()
        for triangle in obj.data.loop_triangles:
            points = [verts[i] for i in triangle.vertices]
            if len(set(points)) != 3:
                raise ValueError("degenerate triangle")
            axis = [i for i in range(3) if len({p[i] for p in points}) == 1]
            if len(axis) != 1:
                raise ValueError("triangle leaves box boundary")
            planes[axis[0], points[0][axis[0]]] += 1
            edges.update((a,b) for a,b in zip(points,points[1:]+points[:1]))
        if len(planes) != 6 or set(planes.values()) != {2} or any(e != 1 or edges.get((b,a)) != 1 for (a,b),e in edges.items()):
            raise ValueError("box triangulation, topology, or winding mismatch")


def run(args):
    generate, mesh, out = args
    write = generate == "generate"
    if write and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("generation requires an existing empty output directory")
    native = json.loads(mesh.read_text()) if write else {}
    board_id = "YAM-WEST-LEFT-BOARD"
    # Reused upstream prototype: no rewriting of the board's .blend.
    bpy.ops.wm.open_mainfile(filepath=str(BLENDS / "west-gate-board-draft.blend"))
    inspect({"WestGateBoard":([0,0,0],DEFS[board_id]["size_mm"])})
    jobs = [("west-gate-board-web","D0",[(DEFS[board_id]["node"], board_id,[0,0,0])])]
    rail_id = "YAM-WEST-LEFT-RAIL"
    jobs += [(DEFS[rail_id]["stem"],"D0",[("WestGateRail",rail_id,[0,0,0])]),
             ("west-gate-left-leaf","D0",[(r["id"],r["source"],r["at_mm"]) for r in ROWS])]
    for stem, rev, placement in jobs:
        expected = {n:(lo,DEFS[key]["size_mm"]) for n,key,lo in placement}
        if write:
            fresh()
            mesh_by_definition = {}
            for n,key,lo in placement:
                if key not in mesh_by_definition:
                    data = native[key]
                    geometry = bpy.data.meshes.new(DEFS[key]["node"])
                    geometry.from_pydata(data["vertices_m"],[],data["triangles"])
                    if geometry.validate():
                        raise ValueError("unexpected repair")
                    geometry.update()
                    material = bpy.data.materials.new("展示用の木色D")
                    material.diffuse_color = (.33,.16,.069,1) if key==board_id else (.20,.082,.039,1)
                    geometry.materials.append(material)
                    mesh_by_definition[key] = geometry
                obj = bpy.data.objects.new(n, mesh_by_definition[key])
                obj.location = [d/1000 for d in lo]
                obj["assembly_revision"], obj["basis"], obj["cad_eligibility"] = rev, "D", "reference_only"
                bpy.context.scene.collection.objects.link(obj)
            bpy.context.view_layer.update()
            bpy.context.preferences.filepaths.save_version = 0
            if stem != "west-gate-board-web":
                bpy.ops.wm.save_as_mainfile(filepath=str(out / (stem + ".blend")), compress=True)
            bpy.ops.export_scene.gltf(filepath=str(out / (stem + ".glb")), export_format="GLB", export_yup=True, export_extras=True)
        source = out if write else BLENDS
        if stem != "west-gate-board-web":
            bpy.ops.wm.open_mainfile(filepath=str(source / (stem + ".blend")))
            units = bpy.context.scene.unit_settings
            if units.system != "METRIC" or units.scale_length != 1:
                raise ValueError("unexpected Blender world unit")
            inspect(expected)
            if stem=="west-gate-left-leaf" and len({o.data for o in bpy.context.scene.objects}) != 2:
                raise ValueError("assembly Blender mesh data not reused")
        fresh()
        bpy.ops.import_scene.gltf(filepath=str((out if write else CAD) / (stem + ".glb")))
        inspect(expected)
        print(f"PASS {stem}: {len(expected)} reimported boxes; six-plane triangulation and oriented edges")
    print("Blender version:",bpy.app.version_string)

if __name__ == "__main__":
    mode, *paths = sys.argv[sys.argv.index("--")+1:]
    if mode not in ("check", "generate") or len(paths)!=(2 if mode=="generate" else 0):
        raise ValueError("use check or generate <native-mesh.json> <empty-directory>")
    run([mode,*([Path(p).resolve() for p in paths] if paths else [None,None])])
