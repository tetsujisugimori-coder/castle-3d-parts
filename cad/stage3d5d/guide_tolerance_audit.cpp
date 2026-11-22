// Read-only OCCT 7.8.1 tolerance and edge-representation census for the fixed Guide.
// Tolerances are observed data, NOT floating-point error bounds or inflated surfaces.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <Geom2d_Line.hxx>
#include <Geom2d_TrimmedCurve.hxx>
#include <Geom_Line.hxx>
#include <Geom_Plane.hxx>
#include <Standard_Version.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Iterator.hxx>
#include <TopLoc_Location.hxx>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <stdexcept>
#include <vector>

namespace {
void number(double x) {
  if (!std::isfinite(x) || x < 0) throw std::runtime_error("BAD_NATIVE_TOLERANCE");
  std::cout << x;
}
void array(const std::vector<double>& a) {
  std::cout << '[';
  for (size_t i=0;i<a.size();++i) {
    if (i) std::cout << ',';
    number(a[i]);
  }
  std::cout << ']';
}
const char* js(bool b) { return b ? "true" : "false"; }
}
int main(int argc, char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if (argc!=2) throw std::runtime_error("USAGE: guide_tolerance_audit fixed_guide.Shape.brp");
    TopoDS_Shape root;
    BRep_Builder builder;
    if (!BRepTools::Read(root,argv[1],builder) || root.IsNull())
      throw std::runtime_error("FIXED_GUIDE_BREP_READ_FAILED");
    TopTools_IndexedMapOfShape faces,edges,vertices;
    TopExp::MapShapes(root,TopAbs_FACE,faces);
    TopExp::MapShapes(root,TopAbs_EDGE,edges);
    TopExp::MapShapes(root,TopAbs_VERTEX,vertices);
    if (faces.Extent()!=10 || edges.Extent()!=24 || vertices.Extent()!=16)
      throw std::runtime_error("NATIVE_TOPOLOGY_CENSUS_CHANGED");
    std::vector<double> ft,et,vt;
    for (int i=1;i<=faces.Extent();++i) ft.push_back(BRep_Tool::Tolerance(TopoDS::Face(faces(i))));
    for (int i=1;i<=edges.Extent();++i) et.push_back(BRep_Tool::Tolerance(TopoDS::Edge(edges(i))));
    for (int i=1;i<=vertices.Extent();++i) vt.push_back(BRep_Tool::Tolerance(TopoDS::Vertex(vertices(i))));
    std::cout << "{\"schema\":1,\"occt\":\""<<OCC_VERSION_COMPLETE
              <<"\",\"counts\":{\"faces\":10,\"edges\":24,\"vertices\":16";
    std::cout << ",\"uses\":48},\"face_tolerances_mm\":";
    array(ft);
    std::cout << ",\"edge_tolerances_mm\":";
    array(et);
    std::cout << ",\"vertex_tolerances_mm\":";
    array(vt);
    std::cout << ",\"uses\":[";
    int uses=0;
    for (int fi=1;fi<=faces.Extent();++fi) {
      const TopoDS_Face f=TopoDS::Face(faces(fi));
      TopLoc_Location floc;
      const auto surface=BRep_Tool::Surface(f,floc);
      const bool isplane=!Handle(Geom_Plane)::DownCast(surface).IsNull();
      int wi=0;
      for (TopoDS_Iterator wIt(f);wIt.More();wIt.Next(),++wi) {
        if(wIt.Value().ShapeType()!=TopAbs_WIRE)throw std::runtime_error("NON_WIRE_FACE_CHILD");
        const TopoDS_Wire w=TopoDS::Wire(wIt.Value());
        int ui=0;
        for (TopoDS_Iterator eIt(w);eIt.More();eIt.Next(),++ui) {
          if(eIt.Value().ShapeType()!=TopAbs_EDGE)throw std::runtime_error("NON_EDGE_WIRE_CHILD");
          const TopoDS_Edge e=TopoDS::Edge(eIt.Value());
          const int ei=edges.FindIndex(e);
          if(ei<=0) throw std::runtime_error("EDGE_NOT_IN_GLOBAL_MAP");
          double a=0,b=0,c=0,d=0;
          Standard_Boolean stored=Standard_False;
          const auto pc=BRep_Tool::CurveOnSurface(e,f,a,b,&stored);
          TopLoc_Location cLoc;
          const auto curve=BRep_Tool::Curve(e,cLoc,c,d);
          const auto trim=Handle(Geom2d_TrimmedCurve)::DownCast(pc);
          const auto pcBase=trim.IsNull()?pc:trim->BasisCurve();
          const bool line2=!Handle(Geom2d_Line)::DownCast(pcBase).IsNull();
          const bool line3=!Handle(Geom_Line)::DownCast(curve).IsNull();
          const bool range_equal=(a==c && b==d && a<b);
          if(uses)std::cout<<',';
          std::cout << "{\"face\":"<<(fi-1)<<",\"wire\":"<<wi<<",\"use\":"<<ui
                    <<",\"edge\":"<<(ei-1)
                    <<",\"stored\":"<<js(stored)
                    <<",\"same_parameter\":"<<js(BRep_Tool::SameParameter(e))
                    <<",\"same_range\":"<<js(BRep_Tool::SameRange(e))
                    <<",\"same_numeric_range\":"<<js(range_equal)
                    <<",\"degenerated\":"<<js(BRep_Tool::Degenerated(e))
                    <<",\"surface_plane\":"<<js(isplane)
                    <<",\"pcurve_line\":"<<js(line2)
                    <<",\"curve_line\":"<<js(line3)
                    <<'}';
          ++uses;
        }
      }
    }
    std::cout << "],\"finite_total_operation_error_upper_mm\":null"
                 ",\"native_full_q_void_inclusion\":\"UNKNOWN\"}\n";
    return uses==48?0:2;
  } catch (const Standard_Failure& e) {
    std::cerr << e.GetMessageString()<<'\n';return 3;
  } catch (const std::exception& e) {
    std::cerr << e.what()<<'\n';return 3;
  }
}
