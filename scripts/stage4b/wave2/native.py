"""Generate or validate Wave 2 FreeCAD/STEP, and tessellate analytic originals."""
import argparse
import json
import math
from pathlib import Path
from itertools import combinations

import FreeCAD as FC
import Part

ROOT = Path(__file__).resolve().parents[3]
D = json.loads((ROOT / "assembly/stage4b-wave2/design.json").read_text())
DEST = ROOT / "cad/stage4b/west-gate-wave2"
V = FC.Vector


def shape(key):
    if key.endswith("POST"):
        return Part.makeBox(300, 300, 3000, V(-150, -150, 0))
    if key.endswith("BEARING"):
        body = Part.makeCylinder(D["bearing_outer_radius"], D["bearing_height"])
        body = body.fuse(Part.makeBox(105, 56, D["bearing_height"], V(-150, -28, 0)))
        return body.cut(Part.makeCylinder(D["bearing_bore_radius"], D["bearing_height"])).removeSplitter()
    pin = Part.makeCylinder(D["pin_radius"], D["arm_top_z"])
    arm = Part.makeBox(130, 50, D["arm_top_z"] - D["arm_base_z"], V(0, -25, D["arm_base_z"]))
    return pin.fuse(arm).removeSplitter()


def assert_valid(s, spec):
    b = s.BoundBox
    actual = [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
    if any(abs(a-b) > .00001 for a,b in zip(actual,spec["bounds_mm"])) or not s.isValid() or len(s.Solids) != 1:
        raise ValueError(f"Invalid solid/dimensions: {spec['node']} {actual}")
    if s.Volume <= 0 or not math.isfinite(s.Volume):
        raise ValueError("Invalid volume")


def check():
    meshes={}
    solids={}
    for key,spec in D["parts"].items():
        stem=spec["stem"]
        d = FC.openDocument(str(DEST / f"{stem}.FCStd"))
        obj=d.getObject(spec["node"])
        if obj is None or obj.PartID != key or obj.Revision != D["revision"]:
            raise ValueError("Wrong native part identity")
        a=obj.Shape.copy()
        FC.closeDocument(d.Name)
        b=Part.read(str(DEST / f"{stem}.step"))
        expected=shape(key)
        for s in [a,b,expected]:
            assert_valid(s,spec)
        for s in [a,b]:
            if abs(s.Volume-expected.Volume)>.001 or s.cut(expected).Volume>.001 or expected.cut(s).Volume>.001:
                raise ValueError(f"native/STEP differs from analytic construction: {stem}")
        vertices,triangles=a.tessellate(.14)
        meshes[key]={"verts":[[x/1000 for x in v] for v in vertices],"triangles":triangles}
        solids[key]=a
        print(f"PASS {key}: FCStd, STEP and analytic solid agree; volume={a.Volume:.3f} mm³")
    bearing=solids["YAM-WEST-BEARING"]
    pin=solids["YAM-WEST-PIVOT"]
    if abs(D["bearing_bore_radius"]-D["pin_radius"]-2) > 1e-8:
        raise ValueError("unexpected radial clearance")
    for deg in range(0,91,5):
        moved=pin.copy()
        moved.rotate(V(),V(0,0,1),deg)
        if bearing.common(moved).Volume>.001:
            raise ValueError(f"unexpected bearing/pin overlap at {deg}°")
    if bearing.common(pin.translated(V(4,0,0))).Volume<=.001:
        raise ValueError("eccentric-pin negative control missed")
    print("PASS pin/bearing: 19 sampled angles, 0 overlaps; shift +4 mm rejected")
    return meshes


def check_assembly(path):
    old=ROOT / "cad/stage4b/west-gate-left"
    native=D["parts"].copy()
    native.update({
        "YAM-WEST-LEFT-BOARD":{"stem":"west-gate-board-draft"},
        "YAM-WEST-LEFT-RAIL":{"stem":"west-gate-rail-draft"}
    })
    source={k:Part.read(str((old if k.startswith("YAM-WEST-LEFT-") else DEST)/(p["stem"]+".step"))) for k,p in native.items()}
    options=json.loads(path.read_text())
    for key,pose in options.items():
        placed={}
        for r in pose["instances"]:
            s=source[r["definition_id"]].copy()
            s.rotate(V(),V(0,0,1),r["yaw_quarters"]*90)
            s.translate(V(*[v*1000 for v in r["translation_m"]]))
            if s.BoundBox.ZMin < -.000001:
                raise ValueError("ground penetration "+r["id"])
            placed[r["id"]]=s
        expected={}
        for side in ["L","R"]:
            for i in range(1,7):
                for j in range(1,3):
                    expected[frozenset([f"{side}-B0{i}",f"{side}-R0{j}"])]=40500
            for i in range(2):
                expected[frozenset([f"{side}-post",f"{side}-bearing-{i}"])]=2800
                expected[frozenset([f"{side}-pin-{i}",f"{side}-R0{i+1}"])]=2500
        contacts={}
        for (n,a),(m,b) in combinations(placed.items(),2):
            overlap=a.BoundBox.intersect(b.BoundBox)
            if overlap and a.common(b).Volume>.001:
                raise ValueError(f"{key}: unexpected positive intersection {n}/{m}")
            k=frozenset([n,m])
            if k in expected:
                area=sum(p.common(q).Area for p in a.Faces for q in b.Faces)
                if abs(area-expected[k]) > .01:
                    raise ValueError(f"{key}: interface area {n}/{m} {area} != {expected[k]}")
                contacts[k]=area
        if len(contacts)!=32 or len(placed)!=26:
            raise ValueError("assembly occurrence/interface count")
        print(f"PASS {key}: 26 solids, 325 pair screens, 32 designated face contacts")
    if sorted(options) != ["both","closed","left","right"]:
        raise ValueError("incomplete fixed-pose report")


def generate():
    for key,spec in D["parts"].items():
        stem=spec["stem"]
        if any((DEST / f"{stem}.{suffix}").exists() for suffix in ["FCStd","step"]):
            raise ValueError("refusing to overwrite a native original")
    for key,spec in D["parts"].items():
        stem=spec["stem"]
        d=FC.newDocument(stem)
        o=d.addObject("Part::Feature",spec["node"])
        o.Shape=shape(key)
        o.addProperty("App::PropertyString","PartID")
        o.PartID=key
        o.addProperty("App::PropertyString","Revision")
        o.Revision=D["revision"]
        d.recompute()
        d.saveAs(str(DEST / f"{stem}.FCStd"))
        Part.export([o],str(DEST / f"{stem}.step"))
        FC.closeDocument(d.Name)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--generate",action="store_true")
    parser.add_argument("--mesh",type=Path)
    parser.add_argument("--poses",type=Path)
    options=parser.parse_args()
    if options.generate:
        generate()
    meshes=check()
    if options.poses:
        check_assembly(options.poses)
    if options.mesh:
        with options.mesh.open("x") as f:
            json.dump(meshes,f)
    print("FreeCAD", ".".join(FC.Version()[:3]), "OCCT", Part.OCC_VERSION)
