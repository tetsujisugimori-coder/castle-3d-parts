// OCCT 7.8.1: exactly five UV classifications of the pinned Guide Face 0.
// Observations only. A finite classifier cannot prove native all-point equality.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepClass_FaceClassifier.hxx>
#include <BRepTools.hxx>
#include <Geom_Surface.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <TopAbs_State.hxx>
#include <Precision.hxx>
#include <Standard_Version.hxx>
#include <gp_Pnt.hxx>
#include <gp_Pnt2d.hxx>
#include <gp_Vec.hxx>
#include <TopLoc_Location.hxx>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <stdexcept>

namespace {
const char* orientation(TopAbs_Orientation o) {
  switch (o) {
    case TopAbs_FORWARD: return "Forward";
    case TopAbs_REVERSED: return "Reversed";
    case TopAbs_INTERNAL: return "Internal";
    case TopAbs_EXTERNAL: return "External";
  }
  return "UNKNOWN";
}
const char* state(TopAbs_State s) {
  switch (s) {
    case TopAbs_IN: return "IN";
    case TopAbs_OUT: return "OUT";
    case TopAbs_ON: return "ON";
    default: return "UNKNOWN";
  }
}
void num(double d) {
  if (!std::isfinite(d)) throw std::runtime_error("NONFINITE_NATIVE_VALUE");
  std::cout << d;
}
void point(const gp_Pnt& p) {
  std::cout << '['; num(p.X());std::cout << ',';num(p.Y());std::cout << ',';
  num(p.Z());std::cout << ']';
}
void vector(const gp_Vec& p) {
  std::cout << '['; num(p.X());std::cout << ',';num(p.Y());std::cout << ',';
  num(p.Z());std::cout << ']';
}
void location(const TopLoc_Location& loc) {
  const auto& t=loc.Transformation();
  std::cout << '[';
  for (int i=1;i<=3;++i) {
    if(i>1)std::cout << ',';
    std::cout << '[';
    for (int j=1;j<=4;++j) {
      if(j>1)std::cout << ',';
      num(t.Value(i,j));
    }
    std::cout << ']';
  }
  std::cout << ",[0,0,0,1]]";
}
struct Query {const char* name;double u;double v;};
const Query queries[] = {
  {"face_interior",5.0,-20.0},
  {"hole_interior",20.0,-20.0},
  {"inner_boundary",9.0,-20.0},
  {"outer_boundary",0.0,-20.0},
  {"face_exterior",-1.0,-20.0}
};
}
int main(int argc,char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if (argc!=2) throw std::runtime_error("USAGE: guide_face0_classifier GUIDEBREP");
    TopoDS_Shape shape;
    BRep_Builder builder;
    if (!BRepTools::Read(shape,argv[1],builder) || shape.IsNull())
      throw std::runtime_error("PINNED_GUIDE_BREP_READ_FAILED");
    TopTools_IndexedMapOfShape faces;
    TopExp::MapShapes(shape,TopAbs_FACE,faces);
    if (faces.Extent()!=10) throw std::runtime_error("EXPECTED_TEN_GUIDE_FACES");
    const TopoDS_Face face=TopoDS::Face(faces(1));
    if (face.Orientation()!=TopAbs_REVERSED)
      throw std::runtime_error("FACE_ZERO_ORIENTATION_CHANGED");
    int wire_count=0;
    for (TopExp_Explorer ex(face,TopAbs_WIRE);ex.More();ex.Next()) ++wire_count;
    if (wire_count!=2) throw std::runtime_error("FACE_ZERO_WIRE_COUNT_CHANGED");
    TopLoc_Location loc;
    const Handle(Geom_Surface)& s=BRep_Tool::Surface(face,loc);
    if (s.IsNull()) throw std::runtime_error("MISSING_FACE_ZERO_SURFACE");
    const double tolerance=BRep_Tool::Tolerance(face);
    const double uv_tol=Precision::PConfusion();
    if (!(tolerance>=0 && std::isfinite(tolerance) && uv_tol>0 && std::isfinite(uv_tol)))
      throw std::runtime_error("INVALID_NATIVE_TOLERANCE");
    double umin,umax,vmin,vmax;
    BRepTools::UVBounds(face,umin,umax,vmin,vmax);
    if (!(umin<umax && vmin<vmax)) throw std::runtime_error("INVALID_FACE_UV_BOUNDS");
    gp_Pnt o,us,vs;
    s->D0(0,0,o);
    s->D0(1,0,us);
    s->D0(0,1,vs);
    const auto transformation=loc.Transformation();
    o.Transform(transformation);
    us.Transform(transformation);
    vs.Transform(transformation);
    const gp_Vec u(o,us),v(o,vs);

    std::cout << "{\"schema\":1,\"occt\":\"" << OCC_VERSION_COMPLETE
              << "\",\"face_index\":0,\"face_count\":" << faces.Extent()
              << ",\"wire_count\":" << wire_count
              << ",\"orientation\":\"" << orientation(face.Orientation())
              << "\",\"natural_restriction\":" << (BRep_Tool::NaturalRestriction(face)?"true":"false")
              << ",\"face_tolerance_mm\":";
    num(tolerance);
    std::cout << ",\"classifier_tolerance_uv\":";
    num(uv_tol);
    std::cout << ",\"uv_bounds\":[";
    num(umin);std::cout<<',';num(umax);std::cout<<',';num(vmin);std::cout<<',';num(vmax);
    std::cout << "],\"surface_type\":\"" << s->DynamicType()->Name()
              << "\",\"surface_location\":";
    location(loc);
    std::cout << ",\"surface_frame_mm\":[";
    point(o);std::cout<<',';vector(u);std::cout<<',';vector(v);
    std::cout << "],\"samples\":[";
    bool comma=false;
    for(const auto& x:queries) {
      BRepClass_FaceClassifier classifier;
      classifier.Perform(face,gp_Pnt2d(x.u,x.v),uv_tol);
      if(comma) std::cout<<',';
      comma=true;
      std::cout << "{\"id\":\"" << x.name << "\",\"uv\":[";
      num(x.u);std::cout<<',';num(x.v);
      std::cout << "],\"state\":\"" << state(classifier.State()) << "\"}";
    }
    std::cout << "],\"sample_count\":5,\"native_full_face_equality\":\"UNKNOWN\"}\n";
    return 0;
  } catch (const Standard_Failure& e) {
    std::cerr << e.GetMessageString() << '\n';return 3;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';return 3;
  }
}
