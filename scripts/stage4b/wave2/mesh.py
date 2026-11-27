"""Build Blender and GLB files from verified FreeCAD tessellation and re-import both."""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[3]
D = json.loads((ROOT / "assembly/stage4b-wave2/design.json").read_text())
CAD = ROOT / "cad/stage4b/west-gate-wave2"
BLENDS = ROOT / "blender/stage4b/wave2"


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1


def metrics(spec, require_units=False):
    objects = list(bpy.context.scene.objects)
    if len(objects) != 1 or objects[0].type != "MESH" or objects[0].name != spec["node"]:
        raise ValueError("unexpected imported object set")
    if require_units and (bpy.context.scene.unit_settings.system != "METRIC" or bpy.context.scene.unit_settings.scale_length != 1):
        raise ValueError("Blender meter units mismatch")
    o=objects[0]
    bpy.context.view_layer.update()
    if any(o.get(k) != v for k,v in {"basis":"D","assembly_revision":"D1","cad_eligibility":"reference_only"}.items()):
        raise ValueError("mesh identity differs")
    bm=bmesh.new()
    try:
        bm.from_mesh(o.data)
        for v in bm.verts:
            v.co=o.matrix_world @ v.co
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=2e-6)
        bounds=[f(v.co[i] for v in bm.verts) for f in [min,max] for i in range(3)]
        if any(not math.isfinite(v) or abs(v-e/1000)>.0001 for v,e in zip(bounds,spec["bounds_mm"])):
            raise ValueError(f"mesh bounds differ {bounds}")
        if any(not e.is_manifold or not e.is_contiguous for e in bm.edges) or any(f.calc_area()<1e-12 for f in bm.faces):
            raise ValueError(f"non-manifold, non-oriented or degenerate surface: {len(bm.verts)} vertices, {len(bm.faces)} faces, {sum(not e.is_manifold for e in bm.edges)} boundary, {sum(not e.is_contiguous for e in bm.edges)} unoriented, {sum(f.calc_area()<1e-12 for f in bm.faces)} small")
        volume=bm.calc_volume(signed=True)
        if not math.isfinite(volume) or volume<=0:
            raise ValueError("invalid oriented mesh volume")
        return (len(bm.verts),len(bm.faces),volume)
    finally:
        bm.free()


def generate(geometry,spec):
    stem=spec["stem"]
    if (CAD/(stem+".glb")).exists() or (BLENDS/(stem+".blend")).exists():
        raise ValueError("refusing to overwrite an authored mesh")
    fresh()
    mesh=bpy.data.meshes.new(spec["node"])
    mesh.from_pydata(geometry["verts"],[],geometry["triangles"])
    mesh.update()
    mat=bpy.data.materials.new("展示木色 D1" if stem.endswith("post") else "展示鉄色 D1")
    mat.diffuse_color=(.35,.19,.095,1) if stem.endswith("post") else (.11,.15,.16,1)
    mat.metallic=0 if stem.endswith("post") else .55
    mat.roughness=.55
    mesh.materials.append(mat)
    obj=bpy.data.objects.new(spec["node"],mesh)
    for k,v in {"basis":"D","assembly_revision":"D1","cad_eligibility":"reference_only"}.items():
        obj[k]=v
    bpy.context.scene.collection.objects.link(obj)
    metrics(spec,True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLENDS/(stem+".blend")),compress=True)
    bpy.ops.export_scene.gltf(filepath=str(CAD/(stem+".glb")),export_format="GLB",export_yup=True,export_extras=True)


mode,*params=sys.argv[sys.argv.index("--")+1:]
if mode not in ["check","generate"] or len(params)!=(mode=="generate"):
    raise ValueError("use check or generate <native-mesh.json>")
native=json.loads(Path(params[0]).read_text()) if params else {}
for ident,spec in D["parts"].items():
    if params:
        generate(native[ident],spec)
    stem=spec["stem"]
    bpy.ops.wm.open_mainfile(filepath=str(BLENDS/(stem+".blend")))
    authored=metrics(spec,True)
    fresh()
    bpy.ops.import_scene.gltf(filepath=str(CAD/(stem+".glb")))
    delivered=metrics(spec)
    if authored[:2]!=delivered[:2] or abs(authored[2]-delivered[2])>1e-10:
        raise ValueError("geometry validation differs after GLB import")
    print(f"PASS {ident}: {delivered}")
print("Blender",bpy.app.version_string)
