# Native proof boundary, Stage 3-D-5C

Checked 2026-11-16 JST. Fixed inputs are identified in PLAN and each raw run. This is a limited proof-obligation implementation, not a successful real-CAD safety certificate.

## What the executable establishes

For a represented line C(t)=c0+t c1, pcurve P(t)=p0+t p1, and plane S(u,v)=o+uU+vV, the verifier requires independent U,V and a nondegenerate parameter interval. It compares constant and linear coefficients using exact rational arithmetic. Equality implies S(P(t))=C(t) for every real t in that interval **in this defined coefficient model**. Discrepancies are enclosed by exact rational interval arithmetic and an L1 upper bound. Unsupported analytic families are UNKNOWN. Native IEEE values are converted to exact rationals of their stored representation, not certified enclosures of an intended geometric real.

The capture records all Vertex/Edge/Wire/Face/Shell/Solid incidences, raw directions, placement, native types, edge ranges, face UV bounds and every pcurve use. Descriptor hashes plus source BRep hash and incidence distinguish identities; integer ordinals are local references, not correspondence proofs. Missing/unreferenced topology rejects the fixed-observation contract. Closed/valid observations and normalized model winding are NOT native material-side proofs.

## Native bridge: unresolved premises, not numerical gaps to fill

1. FreeCAD curveOnSurface uses OCCT BRep_Tool::CurveOnSurface. For a Plane, this can generate rather than retrieve a stored pcurve. The exposed return does not supply isStored. Stored/generated origin is UNKNOWN.
2. SameParameter and SameRange are not exposed by this binding used here. They remain UNKNOWN, not inferred from matching endpoints or samples.
3. Coefficient agreement does not certify extraction rounding, kernel real-set semantics, complete trim coverage, or native tolerance neighborhoods. Face UV bounds alone are not a trim-domain proof.
4. OCCT BRepCheck_Analyzer defaults to a non-exact mode using finite point checks. Shape validity/closed flags and repeated classifier results are not a continuous guarantee.

### Separate material and void obligations

A requires actual native material M to lie inside a conservatively enlarged represented outer set O. B requires the closed moving query Q to lie in the actual complement/through-void with strictly positive separation. A alone does not imply B: an extra unmodelled wall can lie inside O while intersecting Q. Guide inner-wire endpoints and four inner-wall observations are captured, but native trim continuity, material-side orientation and both-end closure are not proven. Both A and B therefore remain UNKNOWN.

The previous model's 1 mm separation is conditional. Representative leaf D2 ordinal 0 spans travel [0,35/32] mm, midpoint 35/64 mm, model movement bound 35/64 mm and represented clearance lower 29/64 mm. This is the first unchanged adaptive leaf of the original128 result, not a new partition. It cannot establish an actual-CAD margin until native material/void correspondence, finite real errors, all-state placement and motion bounds are certified. Native representative NOT_TESTED; no expansion to128.

### Placement

The existing isolated-document observer is rerun without changes and records serialized Shape Location, XML/Object/global/parent Placement and 0/70/140 mm states. Read-only source hashes and isolated-copy hashes are checked. Synthetic chain controls detect double application, omitted parent, wrong order and units, and retain nonidentity matrices. These controls validate the chain contract, not the full native state function. Three matching poses do not establish all-state equivalence. Native all-state equivalence remains UNKNOWN.

## Official implementation sources (read 2026-11-16 JST)

- https://raw.githubusercontent.com/FreeCAD/FreeCAD/1.0.0/src/Mod/Part/App/TopoShapeFacePyImp.cpp : CurveOnSurface wrapper, frame extraction (reviewer inspected L708–734 and L804+).
- https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_8_1/src/BRep/BRep_Tool.hxx : CurveOnSurface plane generation and stored flag, SameParameter/SameRange APIs.
- https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_8_1/src/BRepCheck/BRepCheck_Analyzer.hxx : default exactness and finite checks.

These explain limitations; they are not replacement evidence for the fixed shape. Independent review used the same FreeCAD/OCCT and extractor in a separate process, plus a separately written Fraction coefficient calculation. Independent CAD kernel NOT_TESTED. Physical strength, historicity, GUI and full continuous real-CAD safety are out of scope.
