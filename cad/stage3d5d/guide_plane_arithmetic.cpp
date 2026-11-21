// Fixed Guide raw native Geom_Plane frames: bounded plane evaluation prerequisites.
// Does not certify BRepExtrema optimizer error or Solid occupancy.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <Geom_Plane.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopAbs_Orientation.hxx>
#include <Standard_Version.hxx>
#include <TopLoc_Location.hxx>
#include <gp_Trsf.hxx>
#include <gp_Ax3.hxx>
#include <gp_Pnt.hxx>
#include <gp_Dir.hxx>
#include <cfenv>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <stdexcept>

namespace {
void num(double x) {
  if (!std::isfinite(x)) throw std::runtime_error("NONFINITE_PLANE_COMPONENT");
  std::cout << x;
}
void xyz(double x, double y, double z) {
  std::cout << '[';num(x);std::cout<<',';num(y);std::cout<<',';num(z);std::cout<<']';
}
void point(const gp_Pnt& p) { xyz(p.X(),p.Y(),p.Z()); }
void direction(const gp_Dir& p) { xyz(p.X(),p.Y(),p.Z()); }
const char* ori(TopAbs_Orientation o) {
  if(o==TopAbs_FORWARD)return "Forward";
  if(o==TopAbs_REVERSED)return "Reversed";
  if(o==TopAbs_INTERNAL)return "Internal";
  if(o==TopAbs_EXTERNAL)return "External";
  return "UNKNOWN";
}
}
int main(int argc,char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if (argc!=2) throw std::runtime_error("USAGE: guide_plane_arithmetic guide.Shape.brp");
    if (!std::numeric_limits<double>::is_iec559
        || std::numeric_limits<double>::digits!=53
        || std::fegetround()!=FE_TONEAREST)
      throw std::runtime_error("IEEE_BINARY64_NEAREST_ROUNDING_NOT_CONFIRMED");
    TopoDS_Shape shape;
    BRep_Builder builder;
    if(!BRepTools::Read(shape,argv[1],builder)||shape.IsNull())
      throw std::runtime_error("FIXED_GUIDE_BREP_READ_FAILED");
    TopTools_IndexedMapOfShape faces;
    TopExp::MapShapes(shape,TopAbs_FACE,faces);
    if(faces.Extent()!=10) throw std::runtime_error("GUIDE_FACE_COUNT_CHANGED");
    std::cout<<"{\"schema\":1,\"occt\":\""<<OCC_VERSION_COMPLETE
             <<"\",\"ieee_binary64_round_to_nearest\":true,\"face_count\":10,\"faces\":[";
    for(int i=1;i<=faces.Extent();++i) {
      const TopoDS_Face face=TopoDS::Face(faces(i));
      TopLoc_Location loc;
      const Handle(Geom_Surface)& raw=BRep_Tool::Surface(face,loc);
      Handle(Geom_Plane) plane=Handle(Geom_Plane)::DownCast(raw);
      if(plane.IsNull()) throw std::runtime_error("NON_PLANE_GUIDE_FACE");
      const gp_Trsf tr=loc.Transformation();
      if(tr.Form()!=gp_Translation && tr.Form()!=gp_Identity)
        throw std::runtime_error("NON_TRANSLATION_FACE_LOCATION");
      if(tr.ScaleFactor()!=1.0) throw std::runtime_error("NON_UNIT_NATIVE_LOCATION_SCALE");
      const gp_Ax3& ax=plane->Position();
      const gp_XYZ tv=tr.TranslationPart();
      double u0,u1,v0,v1;
      BRepTools::UVBounds(face,u0,u1,v0,v1);
      if(!(u0<u1&&v0<v1))throw std::runtime_error("INVALID_NATIVE_FACE_UV_BOUNDS");
      if(i>1)std::cout<<',';
      std::cout<<"{\"face_index\":"<<(i-1)
               <<",\"orientation\":\""<<ori(face.Orientation())
               <<"\",\"local_plane_origin_mm\":";
      point(ax.Location());
      std::cout<<",\"native_u_direction\":";
      direction(ax.XDirection());
      std::cout<<",\"native_v_direction\":";
      direction(ax.YDirection());
      std::cout<<",\"translation_mm\":";
      xyz(tv.X(),tv.Y(),tv.Z());
      std::cout<<",\"transform_form\":\""<<(tr.Form()==gp_Identity?"Identity":"Translation")
               <<"\",\"native_face_uv_bounds\":[";
      num(u0);std::cout<<',';num(u1);std::cout<<',';num(v0);std::cout<<',';num(v1);
      std::cout<<"]}";
    }
    std::cout<<"],\"occt_extrema_algorithm_roundoff_bound\":\"UNKNOWN\""
               ",\"real_solid_full_q_occupancy\":\"UNKNOWN\"}\n";
    return 0;
  } catch(const Standard_Failure& e) {
    std::cerr<<e.GetMessageString()<<'\n';return 3;
  } catch(const std::exception& e) {
    std::cerr<<e.what()<<'\n';return 3;
  }
}
