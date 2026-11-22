// Fixed OCCT 7.8.1 Guide: inspect Face trimmed-surface semantics directly.
// Only metadata and topology; does not classify arbitrary points in floating point.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <Geom_Plane.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Wire.hxx>
#include <Standard_Version.hxx>
#include <iostream>
#include <locale>
#include <stdexcept>

static const char* label(TopAbs_Orientation s) {
  if(s==TopAbs_FORWARD)return "Forward";
  if(s==TopAbs_REVERSED)return "Reversed";
  if(s==TopAbs_INTERNAL)return "Internal";
  if(s==TopAbs_EXTERNAL)return "External";
  return "UNKNOWN";
}
int main(int argc,char** argv) {
  std::cout.imbue(std::locale::classic());
  try {
    if(argc!=2)throw std::runtime_error("USAGE: guide_face_semantics fixed.Shape.brp");
    TopoDS_Shape root;BRep_Builder b;
    if(!BRepTools::Read(root,argv[1],b)||root.IsNull())
      throw std::runtime_error("PINNED_BREP_READ_FAILED");
    TopTools_IndexedMapOfShape ss,sh,faces;
    TopExp::MapShapes(root,TopAbs_SOLID,ss);
    TopExp::MapShapes(root,TopAbs_SHELL,sh);
    TopExp::MapShapes(root,TopAbs_FACE,faces);
    if(ss.Extent()!=1||sh.Extent()!=1||faces.Extent()!=10)
      throw std::runtime_error("NATIVE_SOLID_FACE_IDENTITY_CHANGED");
    const TopoDS_Solid solid=TopoDS::Solid(ss(1));
    const TopoDS_Shell shell=TopoDS::Shell(sh(1));
    const bool valid=BRepCheck_Analyzer(solid).IsValid();
    std::cout << "{\"schema\":1,\"occt\":\""<<OCC_VERSION_COMPLETE
              <<"\",\"solid_count\":1,\"shell_count\":1,\"face_count\":10"
              <<",\"solid_orientation\":\""<<label(solid.Orientation())
              <<"\",\"shell_orientation\":\""<<label(shell.Orientation())
              <<"\",\"shell_closed\":"<<(shell.Closed()?"true":"false")
              <<",\"solid_valid_observed\":"<<(valid?"true":"false")
              <<",\"faces\":[";
    for(int i=1;i<=faces.Extent();++i) {
      const TopoDS_Face face=TopoDS::Face(faces(i));
      TopLoc_Location loc;
      Handle(Geom_Plane) plane=Handle(Geom_Plane)::DownCast(BRep_Tool::Surface(face,loc));
      if(plane.IsNull())throw std::runtime_error("NATIVE_FACE_NOT_A_PLANE");
      if(i>1)std::cout<<',';
      std::cout<<"{\"face\":"<<(i-1)
               <<",\"orientation\":\""<<label(face.Orientation())
               <<"\",\"surface_type\":\"Geom_Plane\""
               <<",\"natural_restriction\":"<<(BRep_Tool::NaturalRestriction(face)?"true":"false")
               <<",\"wires\":[";
      int n=0;
      for(TopExp_Explorer ex(face,TopAbs_WIRE);ex.More();ex.Next()) {
        if(n>0)std::cout<<',';
        const TopoDS_Wire wire=TopoDS::Wire(ex.Current());
        std::cout<<"{\"orientation\":\""<<label(wire.Orientation())
                 <<"\",\"closed_flag\":"<<(wire.Closed()?"true":"false")<<"}";
        ++n;
      }
      std::cout<<"],\"wire_count\":"<<n<<"}";
    }
    std::cout<<"],\"native_all_point_classifier_equivalence\":\"UNKNOWN\""
             <<",\"native_full_q_void_inclusion\":\"UNKNOWN\"}\n";
    return (valid&&shell.Closed())?0:2;
  } catch(const Standard_Failure& e){std::cerr<<e.GetMessageString()<<'\n';return 3;}
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 3;}
}
