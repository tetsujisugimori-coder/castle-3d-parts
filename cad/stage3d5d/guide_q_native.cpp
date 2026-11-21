// Fixed Guide BRep versus reused D2 through-void Q, OCCT 7.8.1 observations.
// Shape-to-Q distance is numerical evidence, not a certified all-point bound.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepClass3d_SolidClassifier.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shell.hxx>
#include <TopAbs_State.hxx>
#include <Precision.hxx>
#include <Standard_Version.hxx>
#include <gp_Pnt.hxx>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <stdexcept>

namespace {
void number(const Standard_Real v) {
  if (!std::isfinite(v)) throw std::runtime_error("NONFINITE_NATIVE_VALUE");
  std::cout << v;
}
const char* state(const TopAbs_State s) {
  switch(s) {
    case TopAbs_IN: return "IN";
    case TopAbs_OUT: return "OUT";
    case TopAbs_ON: return "ON";
    default: return "UNKNOWN";
  }
}
const char* orient(const TopAbs_Orientation s) {
  switch(s) {
    case TopAbs_FORWARD: return "Forward";
    case TopAbs_REVERSED: return "Reversed";
    case TopAbs_INTERNAL: return "Internal";
    case TopAbs_EXTERNAL: return "External";
  }
  return "UNKNOWN";
}
}
int main(int argc, char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if(argc!=2) throw std::runtime_error("USAGE: guide_q_native fixed-guide.Shape.brp");
    TopoDS_Shape shape;
    BRep_Builder builder;
    if(!BRepTools::Read(shape,argv[1],builder)||shape.IsNull())
      throw std::runtime_error("PINNED_BREP_READ_FAILED");
    TopTools_IndexedMapOfShape solids,faces,shells;
    TopExp::MapShapes(shape,TopAbs_SOLID,solids);
    TopExp::MapShapes(shape,TopAbs_FACE,faces);
    TopExp::MapShapes(shape,TopAbs_SHELL,shells);
    if(solids.Extent()!=1||faces.Extent()!=10||shells.Extent()!=1)
      throw std::runtime_error("FIXED_GUIDE_TOPOLOGY_CHANGED");
    const TopoDS_Solid solid=TopoDS::Solid(solids(1));
    const TopoDS_Shell shell=TopoDS::Shell(shells(1));
    const bool valid=BRepCheck_Analyzer(solid).IsValid();
    // Fixed D2 Q; Python gate independently reconstructs these 6 values
    // from the pinned four obstacle boxes. Do not change the source CAD.
    const TopoDS_Shape q=BRepPrimAPI_MakeBox(
      gp_Pnt(-201,-115,1000),gp_Pnt(-179,-95,1040)).Shape();
    if(q.IsNull()) throw std::runtime_error("Q_BOX_CREATION_FAILED");
    BRepClass3d_SolidClassifier classifier(solid);
    classifier.Perform(gp_Pnt(-190,-105,1020),Precision::Confusion());
    const TopAbs_State center=classifier.State();
    std::cout << "{\"schema\":1,\"occt\":\"" << OCC_VERSION_COMPLETE
              << "\",\"face_count\":" << faces.Extent()
              << ",\"solid_count\":" << solids.Extent()
              << ",\"shell_count\":" << shells.Extent()
              << ",\"shell_closed_flag\":" << (shell.Closed()?"true":"false")
              << ",\"brepcheck_solid_valid\":" << (valid?"true":"false")
              << ",\"q_closed_box_mm\":[-201,-115,1000,-179,-95,1040]"
              << ",\"one_center_point_mm\":[-190,-105,1020]"
              << ",\"one_center_state\":\"" << state(center)
              << "\",\"one_center_tolerance_mm\":";
    number(Precision::Confusion());
    std::cout << ",\"faces\":[";
    bool all_done=true;
    for(int i=1;i<=faces.Extent();++i) {
      const TopoDS_Face face=TopoDS::Face(faces(i));
      BRepExtrema_DistShapeShape dist(face,q);
      const bool done=dist.IsDone()&&dist.NbSolution()>0;
      if(!done) all_done=false;
      if(i!=1)std::cout << ',';
      std::cout << "{\"face_index\":" << (i-1)
                << ",\"orientation\":\"" << orient(face.Orientation())
                << "\",\"face_tolerance_mm\":";
      number(BRep_Tool::Tolerance(face));
      std::cout << ",\"distance_is_done\":" << (done?"true":"false");
      if(done) {
        std::cout << ",\"boundary_to_q_observed_distance_mm\":";
        number(dist.Value());
        std::cout << ",\"distance_solution_count\":" << dist.NbSolution();
      } else {
        std::cout << ",\"boundary_to_q_observed_distance_mm\":null"
                  << ",\"distance_solution_count\":0";
      }
      std::cout << '}';
    }
    std::cout << "],\"native_all_point_void_inclusion\":\"UNKNOWN\"}\n";
    return (valid&&shell.Closed()&&center==TopAbs_OUT&&all_done)?0:2;
  } catch (const Standard_Failure& e) {
    std::cerr << e.GetMessageString() << '\n';return 3;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';return 3;
  }
}
