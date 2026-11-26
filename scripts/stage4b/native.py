"""Generate rail and assembly from the existing board CAD, or check fixed files.

Always use an empty separately chosen output directory for generation.
FreeCAD uses mm; placements and provenance are explicit in spec.json.
"""
import argparse
import json
import math
from itertools import combinations, product
from pathlib import Path

import FreeCAD as FC
import Part

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cad/stage4b/west-gate-left"
SPEC = json.loads((SRC / "spec.json").read_text())
DEFS = SPEC["definitions"]
ROWS = SPEC["instances"]
EPS = 1e-6


def near(actual, expected, tolerance=EPS):
    if len(actual) != len(expected) or any(not math.isfinite(x) or abs(x-y) > tolerance for x, y in zip(actual, expected)):
        raise ValueError(f"expected {expected}, found {actual}")


def inspect(solid, lo, size):
    """Inspect the bounded analytic rectangular-prism scope, not arbitrary solid equivalence."""
    if not solid.isValid() or len(solid.Solids) != 1:
        raise ValueError("not one valid solid")
    hi = [a+b for a, b in zip(lo, size)]
    box = solid.BoundBox
    near([box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax], [*lo, *hi])
    near([solid.Volume], [math.prod(size)], .01)
    corners = sorted(product(*zip(lo, hi)))
    near([x for p in sorted(tuple(v.Point) for v in solid.Vertexes) for x in p],
         [x for p in corners for x in p])
    if len(solid.Edges) != 12 or len(solid.Faces) != 6 or any(not isinstance(f.Surface, Part.Plane) or len(f.Edges) != 4 for f in solid.Faces):
        raise ValueError("not an untrimmed six-face rectangular box")
    expected_areas = sorted(a*b for a, b in combinations(size, 2)) * 2
    near(sorted(f.Area for f in solid.Faces), sorted(expected_areas), .01)


def definitions(base):
    shapes = {}
    for key, d in DEFS.items():
        root = SRC if key.endswith("BOARD") else base
        doc = FC.openDocument(str(root / (d["stem"] + ".FCStd")))
        obj = doc.getObject(d["node"])
        if obj is None or obj.TypeId != "Part::Box":
            raise ValueError("missing parametric source")
        shape = obj.Shape.copy()
        inspect(shape, (0, 0, 0), d["size_mm"])
        FC.closeDocument(doc.Name)
        inspect(Part.read(str(root / (d["stem"] + ".step"))), (0, 0, 0), d["size_mm"])
        shapes[key] = shape
    return shapes


def compare_pairs(shapes):
    contacts = {}
    for (lhs, a), (rhs, b) in combinations(shapes.items(), 2):
        a_box, b_box = a.BoundBox, b.BoundBox
        key = f"{lhs}/{rhs}"
        if a.common(b).Volume > .001:
            raise ValueError("positive-volume interference: " + key)
        # A two-dimensional intersection of boundary faces is the contact here.
        # This separate check distinguishes a trimmed/edge-only contact from full contact.
        area = sum(af.common(bf).Area for af in a.Faces for bf in b.Faces)
        expect = 40500 if lhs.startswith("B") and rhs.startswith("R") else 0
        near([area], [expect], .01)
        if expect:
            contacts[key] = round(area, 6)
        if lhs.startswith("B") and rhs.startswith("B") and int(rhs[1:])-int(lhs[1:]) == 1:
            near([b_box.XMin-a_box.XMax], [20])
    return contacts


def assembly(base):
    stem = "west-gate-left-leaf"
    doc = FC.openDocument(str(base / (stem + ".FCStd")))
    shapes = {}
    for row in ROWS:
        obj = doc.getObject(row["id"])
        if obj is None or obj.DefinitionId != row["source"]:
            raise ValueError("missing or mismatched assembly occurrence " + row["id"])
        near(tuple(obj.Placement.Base), row["at_mm"])
        near(tuple(obj.Placement.Rotation.Q), [0, 0, 0, 1])
        inspect(obj.Shape, row["at_mm"], DEFS[row["source"]]["size_mm"])
        shapes[row["id"]] = obj.Shape.copy()
    if len(doc.Objects) != len(ROWS):
        raise ValueError("unexpected assembly occurrence")
    FC.closeDocument(doc.Name)
    step = Part.read(str(base / (stem + ".step")))
    if len(step.Solids) != len(ROWS):
        raise ValueError("unexpected STEP occurrence count")
    remaining = list(step.Solids)
    for row in ROWS:
        lo = row["at_mm"]
        match = [s for s in remaining if max(abs(x-y) for x,y in zip(lo,(s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin))) <= EPS]
        if len(match) != 1:
            raise ValueError("ambiguous STEP placement")
        inspect(match[0], lo, DEFS[row["source"]]["size_mm"])
        remaining.remove(match[0])
    bounds = step.BoundBox
    near([bounds.XMin,bounds.YMin,bounds.ZMin,bounds.XMax,bounds.YMax,bounds.ZMax],[-65,0,0,1785,300,2850])
    return compare_pairs(shapes)


def generate(base):
    doc = FC.newDocument("LeftRail")
    d = DEFS["YAM-WEST-LEFT-RAIL"]
    rail = doc.addObject("Part::Box", d["node"])
    rail.Length, rail.Width, rail.Height = d["size_mm"]
    doc.recompute()
    doc.saveAs(str(base / (d["stem"]+".FCStd")))
    Part.export([rail], str(base / (d["stem"]+".step")))
    FC.closeDocument(doc.Name)
    doc = FC.newDocument("WestGateLeft")
    shapes = definitions(base)
    objects = []
    for row in ROWS:
        obj = doc.addObject("Part::Feature", row["id"])
        obj.Shape = shapes[row["source"]].copy()
        obj.addProperty("App::PropertyString", "DefinitionId", "Provenance")
        obj.DefinitionId = row["source"]
        obj.Placement.Base = FC.Vector(*row["at_mm"])
        objects.append(obj)
    doc.recompute()
    doc.saveAs(str(base / "west-gate-left-leaf.FCStd"))
    Part.export(objects, str(base / "west-gate-left-leaf.step"))
    FC.closeDocument(doc.Name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", type=Path)
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--negative", action="store_true")
    args = parser.parse_args()
    base = args.generate.resolve() if args.generate else SRC
    if args.generate:
        if not base.is_dir() or any(base.iterdir()):
            raise ValueError("generation requires an existing empty output directory")
        generate(base)
    shapes = definitions(base)
    contacts = assembly(base)
    if args.negative:
        sample = {}
        for row in ROWS:
            solid = shapes[row["source"]].copy()
            solid.translate(FC.Vector(*row["at_mm"]))
            sample[row["id"]] = solid
        for key, offset, expected in [("R01",(0,-1,0),"positive-volume interference"),
                                      ("R01",(0,1,0),"expected [40500]"),
                                      ("B02",(1,0,0),"expected [20]")]:
            fault = dict(sample)
            fault[key] = sample[key].copy()
            fault[key].translate(FC.Vector(*offset))
            try:
                compare_pairs(fault)
            except ValueError as e:
                if expected not in str(e):
                    raise
                print("REJECTED:", key, offset, str(e))
            else:
                raise ValueError("accepted deliberate native fault")
    if args.mesh:
        result = {}
        for key, shape in shapes.items():
            points, triangles = shape.tessellate(.1)
            result[key] = {"vertices_m": [[x/1000 for x in point] for point in points],
                           "triangles": triangles}
        with args.mesh.open("x") as f:
            json.dump(result, f, indent=2)
    print(json.dumps({"freecad":".".join(FC.Version()[:3]),"occt":Part.OCC_VERSION,"boxes":10,
        "step_assembly_solids":8,"pairs":28,"intentional_contacts_mm2":contacts,
        "expected_board_gaps_mm":[20]*5,"size_mm":[1850,300,2850]},indent=2))

if __name__ == "__main__":
    main()
