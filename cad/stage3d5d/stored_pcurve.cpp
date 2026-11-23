// Collect stored OCCT representations from a fixed BRep. No CAD writes.
// The Python gate proves identities on the exposed coefficients, separately
// from any native-real set, tolerance, or motion claim.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRep_TEdge.hxx>
#include <BRep_ListIteratorOfListOfCurveRepresentation.hxx>
#include <BRepTools.hxx>
#include <BRepTools_WireExplorer.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <Geom2d_Line.hxx>
#include <Geom2d_TrimmedCurve.hxx>
#include <Geom_Line.hxx>
#include <Geom_Plane.hxx>
#include <Standard_Version.hxx>
#include <TopExp.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Iterator.hxx>
#include <TopoDS_Wire.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <gp_Pln.hxx>
#include <gp_Trsf.hxx>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <set>
#include <sstream>
#include <iostream>
#include <limits>
#include <locale>
#include <stdexcept>
#include <string>

namespace {
const char* orientation(TopAbs_Orientation o) {
  switch(o) {
    case TopAbs_FORWARD:return "Forward";
    case TopAbs_REVERSED:return "Reversed";
    case TopAbs_INTERNAL:return "Internal";
    case TopAbs_EXTERNAL:return "External";
  }
  throw std::runtime_error("UNKNOWN_ORIENTATION");
}
const char* yes(bool v) { return v ? "true" : "false"; }
void num(double v) {
  if (!std::isfinite(v)) throw std::runtime_error("NONFINITE_COEFFICIENT");
  std::cout << v;
}
template<class V> void v2(const V& v) {
  std::cout << '['; num(v.X()); std::cout << ','; num(v.Y()); std::cout << ']';
}
template<class V> void v3(const V& v) {
  std::cout << '['; num(v.X()); std::cout << ','; num(v.Y()); std::cout << ','; num(v.Z()); std::cout << ']';
}
void loc(const TopLoc_Location& l) {
  const auto& t=l.Transformation();
  std::cout << '[';
  for(int i=1;i<=3;++i) {
    if(i>1)std::cout << ',';
    std::cout << '[';
    for(int j=1;j<=4;++j) {if(j>1)std::cout << ',';num(t.Value(i,j));}
    std::cout << ']';
  }
  std::cout << ",[0,0,0,1]]";
}
void range(double a,double b) {std::cout << '[';num(a);std::cout << ',';num(b);std::cout << ']';}

void loaded_occt() {
  // Actual loaded libraries, not ldd predictions. The selected runner is Linux.
  std::ifstream maps("/proc/self/maps");
  if(!maps)throw std::runtime_error("PROC_MAPS_UNAVAILABLE");
  std::set<std::string> loaded;
  std::string record;
  while(std::getline(maps,record)) {
    const auto slash=record.find('/');
    if(slash==std::string::npos)continue;
    const auto path=record.substr(slash);
    const auto base=path.substr(path.find_last_of('/')+1);
    if(base.rfind("libTK",0)==0 && base.find(".so")!=std::string::npos)loaded.insert(path);
  }
  if(loaded.empty())throw std::runtime_error("OCCT_RUNTIME_MAP_EMPTY");
  std::cout << '[';
  bool sep=false;
  for(const auto& path:loaded) {
    if(sep)std::cout << ',';
    sep=true;std::cout << std::quoted(path);
  }
  std::cout << ']';
}

struct Reps {
  int indexed_count=0, indexed_matches=0, candidates=0, matching_3d_count=0, matching_2d_count=0;
  double indexed_lo=0,indexed_hi=0;
  int selected_2d=-1, selected_3d=-1, tool_index=-1;
  bool seam=false;
  TopLoc_Location relative2d, relative3d;
};
Reps enumerate(const TopoDS_Edge& e, const TopoDS_Face& f, const Handle(Geom2d_Curve)& pc,
               double lo, double hi, const Handle(Geom_Surface)& s, const TopLoc_Location& fLoc,
               const Handle(Geom_Curve)& c, const TopLoc_Location& cLoc) {
  Reps r;
  // The indexed API enumerates stored curve-on-surface representations, not
  // the planar projection fallback of the face-specific accessor.
  for(int rank=1;rank<=1024;++rank) {
    Handle(Geom2d_Curve) c2;
    Handle(Geom_Surface) surf;
    TopLoc_Location where;
    double a=0,b=0;
    BRep_Tool::CurveOnSurface(e,c2,surf,where,a,b,rank);
    if(c2.IsNull()&&surf.IsNull())break;
    if(rank==1024 || c2.IsNull() || surf.IsNull())throw std::runtime_error("INDEXED_REP_INCOMPLETE");
    ++r.indexed_count;
    if(surf==s && where==fLoc) {
      ++r.candidates;
      if(c2==pc && a==lo && b==hi) {
        ++r.indexed_matches;
        r.tool_index=rank;r.indexed_lo=a;r.indexed_hi=b;
      }
    }
  }
  r.seam=BRep_Tool::IsClosed(e,f);
  auto te=Handle(BRep_TEdge)::DownCast(e.TShape());
  if(te.IsNull())throw std::runtime_error("NOT_BREP_TEDGE");
  int i=0;
  for(BRep_ListIteratorOfListOfCurveRepresentation it(te->Curves());it.More();it.Next()) {
    ++i;
    const auto& rep=it.Value();
    auto global=e.Location()*rep->Location();
    if(rep->IsCurveOnSurface() && rep->Surface()==s && global==fLoc &&
       !pc.IsNull() && rep->PCurve()==pc) {++r.matching_2d_count;r.selected_2d=i;r.relative2d=rep->Location();}
    if(rep->IsCurve3D() && !c.IsNull() && rep->Curve3D()==c && global==cLoc) {
      ++r.matching_3d_count;r.selected_3d=i;r.relative3d=rep->Location();
    }
  }
  return r;
}
bool row(const TopoDS_Face& f, const TopoDS_Wire& w, const TopoDS_Edge& e,
         int fi,int wi,int ui,int ei) {
  double a=0,b=0,c=0,d=0;
  Standard_Boolean stored=Standard_False;
  auto pcurve=BRep_Tool::CurveOnSurface(e,f,a,b,&stored);
  TopLoc_Location cLoc,fLoc;
  auto curve=BRep_Tool::Curve(e,cLoc,c,d);
  auto surface=BRep_Tool::Surface(f,fLoc);
  auto reps=enumerate(e,f,pcurve,a,b,surface,fLoc,curve,cLoc);
  int order=0, ordered_index=-1, ordered_matches=0;
  for(BRepTools_WireExplorer ordered(w);ordered.More();ordered.Next(),++order) {
    if(ordered.Current().IsEqual(e)) {++ordered_matches;ordered_index=order;}
  }
  auto trim=Handle(Geom2d_TrimmedCurve)::DownCast(pcurve);
  auto line2=Handle(Geom2d_Line)::DownCast(trim.IsNull()?pcurve:trim->BasisCurve());
  auto line3=Handle(Geom_Line)::DownCast(curve);
  auto plane=Handle(Geom_Plane)::DownCast(surface);
  const char* status=!stored ? "NOT_STORED" :
    reps.indexed_matches!=1 || reps.candidates!=1 || reps.matching_3d_count!=1 ||
    reps.matching_2d_count!=1 || reps.selected_2d<1 || reps.selected_3d<1 || reps.seam || ordered_matches!=1 ? "AMBIGUOUS_OR_MISSING_REPRESENTATION" :
    line2.IsNull() || line3.IsNull() || plane.IsNull() ? "UNSUPPORTED_GEOMETRY" :
    !BRep_Tool::SameParameter(e) || !BRep_Tool::SameRange(e) ||
    BRep_Tool::Degenerated(e) || !(a<b && a==c && b==d) ||
    (!trim.IsNull() && (trim->FirstParameter()!=a || trim->LastParameter()!=b)) ? "UNSUPPORTED_RANGE_OR_FLAGS" :
    cLoc.Transformation().ScaleFactor()!=1 || fLoc.Transformation().ScaleFactor()!=1 ?
       "UNSUPPORTED_NONUNIT_LOCATION_SCALE" :
    "CAPTURED";
  std::cout << "{\"face\":" << fi << ",\"wire\":" << wi << ",\"use\":" << ui
            << ",\"ordered_use\":" << ordered_index << ",\"ordered_matches\":" << ordered_matches
            << ",\"edge\":" << ei << ",\"orientation\":\"" << orientation(e.Orientation())
            << "\",\"face_orientation\":\"" << orientation(f.Orientation())
            << "\",\"wire_orientation\":\"" << orientation(w.Orientation())
            << "\",\"stored\":" << yes(stored)
            << ",\"indexed_count\":" << reps.indexed_count << ",\"indexed_matches\":" << reps.indexed_matches
            << ",\"surface_location_candidate_count\":" << reps.candidates
            << ",\"matching_3d_count\":" << reps.matching_3d_count
            << ",\"selected_2d_matches\":" << reps.matching_2d_count
            << ",\"selected_2d_rep_ordinal\":" << reps.selected_2d
            << ",\"selected_3d_rep_ordinal\":" << reps.selected_3d
            << ",\"indexed_tool_rank\":" << reps.tool_index
            << ",\"seam\":" << yes(reps.seam)
            << ",\"same_parameter\":" << yes(BRep_Tool::SameParameter(e))
            << ",\"same_range\":" << yes(BRep_Tool::SameRange(e))
            << ",\"degenerated\":" << yes(BRep_Tool::Degenerated(e))
            << ",\"pcurve_type\":\"" << (pcurve.IsNull()?"null":pcurve->DynamicType()->Name())
            << "\",\"curve_type\":\"" << (curve.IsNull()?"null":curve->DynamicType()->Name())
            << "\",\"surface_type\":\"" << (surface.IsNull()?"null":surface->DynamicType()->Name())
            << "\",\"status\":\"" << status << "\",\"edge_location\":";
  loc(cLoc);std::cout << ",\"surface_location\":";loc(fLoc);
  std::cout << ",\"edge_topological_location\":";loc(e.Location());
  std::cout << ",\"face_topological_location\":";loc(f.Location());
  std::cout << ",\"wire_topological_location\":";loc(w.Location());
  std::cout << ",\"relative_rep_2d_location\":";loc(reps.relative2d);
  std::cout << ",\"relative_rep_3d_location\":";loc(reps.relative3d);
  if(reps.indexed_matches==1){std::cout << ",\"indexed_range\":";range(reps.indexed_lo,reps.indexed_hi);}
  if(!pcurve.IsNull()){std::cout << ",\"pcurve_range\":";range(a,b);}
  if(!curve.IsNull()){std::cout << ",\"curve_range\":";range(c,d);}
  if(!trim.IsNull()){std::cout << ",\"pcurve_intrinsic_range\":";range(trim->FirstParameter(),trim->LastParameter());}
  if(!line2.IsNull()) {
    std::cout << ",\"pcurve\":[";v2(line2->Position().Location());std::cout<<',';v2(line2->Position().Direction());std::cout<<']';
  }
  if(!line3.IsNull()) {
    const auto t=cLoc.Transformation();
    std::cout << ",\"curve\":[";v3(line3->Position().Location().Transformed(t));std::cout<<',';v3(line3->Position().Direction().Transformed(t));std::cout<<']';
  }
  if(!plane.IsNull()) {
    const auto t=fLoc.Transformation();
    std::cout << ",\"plane\":["; v3(plane->Position().Location().Transformed(t));
    std::cout << ',';v3(plane->Position().XDirection().Transformed(t));
    std::cout << ',';v3(plane->Position().YDirection().Transformed(t));std::cout << ']';
  }
  std::cout << '}';
  return std::string(status)=="CAPTURED";
}
}

int main(int argc,char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if(argc==2 && std::string(argv[1])=="--projected-control") {
      const auto f=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,0,0),gp_Dir(0,0,1))).Face();
      const auto e=BRepBuilderAPI_MakeEdge(gp_Pnt(1,1,0),gp_Pnt(3,1,0)).Edge();
      double lo=0,hi=0;Standard_Boolean stored=Standard_True;
      auto curve=BRep_Tool::CurveOnSurface(e,f,lo,hi,&stored);
      const bool negative=!curve.IsNull() && !stored && lo<hi;
      std::cout << "{\"schema\":1,\"mode\":\"projected-control\",\"occt\":\"" << OCC_VERSION_COMPLETE
                << "\",\"pcurve_present\":"<<yes(!curve.IsNull())<<",\"stored\":"<<yes(stored)
                << ",\"expected_refusal\":"<<yes(negative)<<"}\n";
      return negative?0:3;
    }
    if(argc!=3 && argc!=4)throw std::runtime_error("USAGE: stored_pcurve BREP pilot|all [X_TRANSLATION_MM]");
    const std::string mode=argv[2];
    if(mode!="pilot" && mode!="all")throw std::runtime_error("INVALID_MODE");
    TopoDS_Shape shape;
    BRep_Builder builder;
    if(!BRepTools::Read(shape,argv[1],builder)||shape.IsNull())throw std::runtime_error("BREP_READ_FAILED");
    if(argc==4) {
      std::size_t parsed=0;const std::string arg=argv[3];double dx=std::stod(arg,&parsed);
      if(parsed!=arg.size() || !std::isfinite(dx))throw std::runtime_error("INVALID_TRANSLATION");
      gp_Trsf t;t.SetTranslation(gp_Vec(dx,0,0));
      shape.Move(TopLoc_Location(t));
    }
    TopTools_IndexedMapOfShape faces,edges;
    TopExp::MapShapes(shape,TopAbs_FACE,faces);TopExp::MapShapes(shape,TopAbs_EDGE,edges);
    if(faces.Extent()==0 || edges.Extent()==0)throw std::runtime_error("NO_FACE_OR_EDGE");
    std::cout << "{\"schema\":1,\"mode\":\"" << mode << "\",\"occt\":\"" << OCC_VERSION_COMPLETE
              << "\",\"faces\":" << faces.Extent() << ",\"edges\":" << edges.Extent() << ",\"uses\":[";
    int count=0;
    bool ok=true;
    for(int fi=1;fi<=faces.Extent()&&(mode=="all"||count==0);++fi) {
      const auto f=TopoDS::Face(faces(fi));
      int wi=0;
      for(TopoDS_Iterator fw(f);fw.More()&&(mode=="all"||count==0);fw.Next()) {
        if(fw.Value().ShapeType()!=TopAbs_WIRE)throw std::runtime_error("NON_WIRE_FACE_CHILD");
        const auto w=TopoDS::Wire(fw.Value());
        int ui=0;
        for(TopoDS_Iterator we(w);we.More()&&(mode=="all"||count==0);we.Next()) {
          if(we.Value().ShapeType()!=TopAbs_EDGE)throw std::runtime_error("NON_EDGE_WIRE_CHILD");
          const auto e=TopoDS::Edge(we.Value());
          const int ei=edges.FindIndex(e);
          if(ei==0)throw std::runtime_error("EDGE_NOT_MAPPED");
          if(count++)std::cout << ',';
          if(!row(f,w,e,fi-1,wi,ui++,ei-1))ok=false;
        }
        ++wi;
      }
    }
    std::cout << "],\"use_count\":" << count << ",\"loaded_occt_libraries\":";loaded_occt();std::cout << "}\n";
    return ok && count>0?0:2;
  } catch(const Standard_Failure& ex) {
    std::cerr << ex.GetMessageString() << '\n';
    return 3;
  } catch(const std::exception& ex) {
    std::cerr << ex.what() << '\n';
    return 3;
  }
}
