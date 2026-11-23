// One-pass diagnostic: interpose OCCT 7.8.1 C++ member symbols at runtime.
// This is NOT a mathematical error bound and does not modify BRep geometry.
// If the dynamic linker does not route actual calls through these hooks,
// validation rejects the trace rather than calling a model replay "native".
#include <BRepClass_FaceExplorer.hxx>
#include <BRepClass_FClass2dOfFClassifier.hxx>
#include <BRepClass_Intersector.hxx>
#include <BRepClass_Edge.hxx>
#include <BRep_Tool.hxx>
#include <Geom2d_Curve.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopAbs_Orientation.hxx>
#include <gp_Lin2d.hxx>
#include <gp_Pnt2d.hxx>
#include <gp_Dir2d.hxx>
#include <dlfcn.h>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <locale>
#include <sstream>
#include <stdexcept>

namespace {
thread_local const char* active = "UNMATCHED";
thread_local unsigned long seq = 0;
const char* query(double u,double v) {
  if (u==5 && v==-20) return "face_interior";
  if (u==20 && v==-20) return "hole_interior";
  if (u==9 && v==-20) return "inner_boundary";
  if (u==0 && v==-20) return "outer_boundary";
  if (u==-1 && v==-20) return "face_exterior";
  return "UNMATCHED";
}
const char* state(TopAbs_State s) {
  if(s==TopAbs_IN)return "IN";
  if(s==TopAbs_OUT)return "OUT";
  if(s==TopAbs_ON)return "ON";
  return "UNKNOWN";
}
const char* orient(TopAbs_Orientation s) {
  if(s==TopAbs_FORWARD)return "Forward";
  if(s==TopAbs_REVERSED)return "Reversed";
  if(s==TopAbs_INTERNAL)return "Internal";
  if(s==TopAbs_EXTERNAL)return "External";
  return "UNKNOWN";
}
std::string uv(const gp_Pnt2d& p) {
  std::ostringstream out;
  out.imbue(std::locale::classic());
  out<<std::setprecision(17)<<'['<<p.X()<<','<<p.Y()<<']';
  return out.str();
}
std::string ray(const gp_Lin2d& l) {
  std::ostringstream out;
  out.imbue(std::locale::classic());
  out<<"{\"origin\":"<<uv(l.Location())<<",\"direction\":["
     <<std::setprecision(17)<<l.Direction().X()<<','<<l.Direction().Y()<<"]}";
  return out.str();
}
int ordinal(const BRepClass_Edge& e) {
  TopTools_IndexedMapOfShape edges;
  TopExp::MapShapes(e.Face(),TopAbs_EDGE,edges);
  return edges.FindIndex(e.Edge());
}
std::string edge(const BRepClass_Edge& e) {
  std::ostringstream out;out.imbue(std::locale::classic());
  out<<std::setprecision(17)<<"\"face_local_edge_ordinal\":"<<ordinal(e)
     <<",\"edge_orientation\":\""<<orient(e.Edge().Orientation())<<"\""
     <<",\"use_bbox\":"<<(e.UseBndBox()?"true":"false")
     <<",\"gap_check_tolerance\":"<<e.MaxTolerance();
  Standard_Real a=0,b=0;
  Handle(Geom2d_Curve) c=BRep_Tool::CurveOnSurface(e.Edge(),e.Face(),a,b);
  if(!c.IsNull()) {
    out<<",\"edge_parameter_range\":["<<a<<','<<b<<']'
       <<",\"edge_start_uv\":"<<uv(c->Value(a))
       <<",\"edge_end_uv\":"<<uv(c->Value(b));
  } else out<<",\"pcurve_missing\":true";
  return out.str();
}
void write_event(const std::string& body) {
  const char* path=std::getenv("CASTLE_FACE0_TRACE");
  if(!path || !*path) return;
  std::ofstream out(path,std::ios::app);
  out.imbue(std::locale::classic());
  if(!out) {std::abort();}
  out<<"{\"seq\":"<<(++seq)<<",\"query\":\""<<active<<"\","<<body<<"}\n";
  out.flush();
  if(!out) std::abort();
}
template<class F> F original(const char* symbol) {
  dlerror();
  void* ptr=dlsym(RTLD_NEXT,symbol);
  if(!ptr || dlerror()) std::abort();
  return reinterpret_cast<F>(ptr);
}
}
Standard_Boolean BRepClass_FaceExplorer::OtherSegment(
    const gp_Pnt2d& p,gp_Lin2d& line,Standard_Real& parameter) {
  using Fn=Standard_Boolean (*)(BRepClass_FaceExplorer*,const gp_Pnt2d&,gp_Lin2d&,Standard_Real&);
  static Fn orig=original<Fn>("_ZN22BRepClass_FaceExplorer12OtherSegmentERK8gp_Pnt2dR8gp_Lin2dRd");
  active=query(p.X(),p.Y());
  const Standard_Boolean chosen=orig(this,p,line,parameter);
  std::ostringstream o;o.imbue(std::locale::classic());
  o<<std::setprecision(17)
   <<"\"event\":\"ray_choice\",\"candidate_point_uv\":"<<uv(p)
   <<",\"selected\":"<<(chosen?"true":"false")
   <<",\"ray\":"<<ray(line)
   <<",\"ray_length\":"<<parameter;
  write_event(o.str());
  return chosen;
}
void BRepClass_Intersector::Perform(const gp_Lin2d& line,
    const Standard_Real parameter,const Standard_Real tolerance,const BRepClass_Edge& e) {
  using Fn=void (*)(BRepClass_Intersector*,const gp_Lin2d&,Standard_Real,Standard_Real,const BRepClass_Edge&);
  static Fn orig=original<Fn>("_ZN21BRepClass_Intersector7PerformERK8gp_Lin2dddRK14BRepClass_Edge");
  active=query(line.Location().X(),line.Location().Y());
  orig(this,line,parameter,tolerance,e);
  std::ostringstream o;o.imbue(std::locale::classic());
  o<<std::setprecision(17)<<"\"event\":\"intersector\",\"ray\":"<<ray(line)
   <<",\"ray_length\":"<<parameter<<",\"tol_argument\":"<<tolerance
   <<','<<edge(e)<<",\"is_done\":"<<(IsDone()?"true":"false");
  if(IsDone())o<<",\"intersection_points\":"<<NbPoints()
               <<",\"intersection_segments\":"<<NbSegments();
  write_event(o.str());
}
void BRepClass_FClass2dOfFClassifier::Compare(
    const BRepClass_Edge& e,const TopAbs_Orientation orientation) {
  using Fn=void (*)(BRepClass_FClass2dOfFClassifier*,const BRepClass_Edge&,TopAbs_Orientation);
  static Fn orig=original<Fn>("_ZN31BRepClass_FClass2dOfFClassifier7CompareERK14BRepClass_Edge18TopAbs_Orientation");
  orig(this,e,orientation);
  std::ostringstream o;o.imbue(std::locale::classic());
  o<<std::setprecision(17)
   <<"\"event\":\"compare\",\"compare_orientation\":\""<<orient(orientation)<<"\""
   <<','<<edge(e)
   <<",\"closest_index\":"<<ClosestIntersection()
   <<",\"state_after\":\""<<state(State())<<"\"";
  write_event(o.str());
}
