// Fixed Guide BRep: direct Solid -> Shell -> Face -> Wire -> Edge containment.
// Independent native topology census, not proof of floating-point Solid occupancy.
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Iterator.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Vertex.hxx>
#include <Standard_Version.hxx>
#include <gp_Pnt.hxx>
#include <iostream>
#include <algorithm>
#include <cmath>
#include <utility>
#include <iomanip>
#include <locale>
#include <limits>
#include <vector>
#include <set>
#include <stdexcept>

namespace {
const char* ori(TopAbs_Orientation o) {
  switch(o) {
    case TopAbs_FORWARD:return "Forward";
    case TopAbs_REVERSED:return "Reversed";
    case TopAbs_INTERNAL:return "Internal";
    case TopAbs_EXTERNAL:return "External";
  }
  return "UNKNOWN";
}
struct EdgeUse { int face; int wire; const char* orientation; };
}
int main(int argc,char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if(argc!=2) throw std::runtime_error("USAGE: guide_solid_hierarchy guide.Shape.brp");
    TopoDS_Shape root;
    BRep_Builder b;
    if(!BRepTools::Read(root,argv[1],b)||root.IsNull())
      throw std::runtime_error("FIXED_BREP_READ_FAILED");
    TopTools_IndexedMapOfShape solids,shells,faces,wires,edges,verts;
    TopExp::MapShapes(root,TopAbs_SOLID,solids);
    TopExp::MapShapes(root,TopAbs_SHELL,shells);
    TopExp::MapShapes(root,TopAbs_FACE,faces);
    TopExp::MapShapes(root,TopAbs_WIRE,wires);
    TopExp::MapShapes(root,TopAbs_EDGE,edges);
    TopExp::MapShapes(root,TopAbs_VERTEX,verts);
    if(solids.Extent()!=1||shells.Extent()!=1||faces.Extent()!=10||
       wires.Extent()!=12||edges.Extent()!=24||verts.Extent()!=16)
      throw std::runtime_error("FIXED_HIERARCHY_COUNTS_CHANGED");
    TopoDS_Solid solid=TopoDS::Solid(solids(1));
    TopoDS_Shell shell=TopoDS::Shell(shells(1));
    int directShells=0;
    for(TopoDS_Iterator it(solid,Standard_True,Standard_True);it.More();it.Next()) {
      const TopoDS_Shape& x=it.Value();
      if(x.ShapeType()!=TopAbs_SHELL||!x.IsSame(shell))
        throw std::runtime_error("SOLID_HAS_UNEXPECTED_DIRECT_CHILD");
      ++directShells;
    }
    if(directShells!=1)throw std::runtime_error("SOLID_SHELL_EXHAUSTIVENESS_FAIL");
    std::vector<int> directFace(11,0),wireParents(13,0);
    for(TopoDS_Iterator it(shell,Standard_True,Standard_True);it.More();it.Next()) {
      const TopoDS_Shape& x=it.Value();
      if(x.ShapeType()!=TopAbs_FACE)throw std::runtime_error("SHELL_NON_FACE_CHILD");
      const int fi=faces.FindIndex(x);
      if(fi<1||fi>10||++directFace[fi]!=1||
          x.Orientation()!=faces(fi).Orientation())
        throw std::runtime_error("SHELL_FACE_DUPLICATE_OR_ORIENTATION_MISMATCH");
    }
    for(int i=1;i<=10;++i)
      if(directFace[i]!=1)throw std::runtime_error("SHELL_FACE_OMITTED");
    std::vector<std::vector<EdgeUse>> edgeUses(25);
    std::vector<std::vector<int>> edgeVertex(25);
    std::vector<int> vertexEdgeDegree(17,0);
    std::vector<std::vector<int>> faceWires(11),wireEdges(13);
    std::vector<std::vector<const char*>> wireOrientations(13);
    for(int fi=1;fi<=10;++fi) {
      TopoDS_Face face=TopoDS::Face(faces(fi));
      for(TopoDS_Iterator wit(face,Standard_True,Standard_True);wit.More();wit.Next()) {
        const TopoDS_Shape& w=wit.Value();
        if(w.ShapeType()!=TopAbs_WIRE)throw std::runtime_error("FACE_NON_WIRE_CHILD");
        const int wi=wires.FindIndex(w);
        if(wi<1||wi>12||++wireParents[wi]!=1)
          throw std::runtime_error("WIRE_ORPHAN_OR_DUPLICATE");
        faceWires[fi].push_back(wi);
        std::set<int> localEdges;
        for(TopoDS_Iterator eit(w,Standard_True,Standard_True);eit.More();eit.Next()) {
          const TopoDS_Shape& s=eit.Value();
          if(s.ShapeType()!=TopAbs_EDGE)throw std::runtime_error("WIRE_NON_EDGE_CHILD");
          int ei=edges.FindIndex(s);
          if(ei<1||ei>24||!localEdges.insert(ei).second)
            throw std::runtime_error("WIRE_INVALID_OR_DUPLICATE_EDGE");
          edgeUses[ei].push_back({fi,wi,ori(s.Orientation())});
          wireEdges[wi].push_back(ei);
          wireOrientations[wi].push_back(ori(s.Orientation()));
        }
        if(localEdges.size()!=4)throw std::runtime_error("NON_FOUR_EDGE_NATIVE_WIRE");
      }
      if(faceWires[fi].size()!=(fi==1||fi==10?2u:1u))
        throw std::runtime_error("FACE_WIRE_CENSUS_CHANGED");
    }
    for(int wi=1;wi<=12;++wi)
      if(wireParents[wi]!=1)throw std::runtime_error("WIRE_MISSING_FROM_FACES");
    std::set<std::pair<int,int>> facePairs;
    for(int ei=1;ei<=24;++ei) {
      if(edgeUses[ei].size()!=2||
          edgeUses[ei][0].face==edgeUses[ei][1].face)
        throw std::runtime_error("EDGE_NOT_SHARED_BY_DISTINCT_TWO_FACES");
      const int a=edgeUses[ei][0].face,b=edgeUses[ei][1].face;
      if(!facePairs.insert(std::minmax(a,b)).second)
        throw std::runtime_error("TWO_EDGES_WITH_SAME_ADJACENT_FACES");
      TopoDS_Vertex va,vb;
      TopExp::Vertices(TopoDS::Edge(edges(ei)),va,vb,Standard_True);
      if(va.IsNull()||vb.IsNull())throw std::runtime_error("OPEN_OR_MISSING_NATIVE_VERTEX");
      int aidx=verts.FindIndex(va),bidx=verts.FindIndex(vb);
      if(aidx<1||bidx<1||aidx==bidx)
        throw std::runtime_error("INVALID_NATIVE_EDGE_ENDPOINT");
      edgeVertex[ei]={aidx,bidx};
      ++vertexEdgeDegree[aidx];++vertexEdgeDegree[bidx];
    }
    for(int i=1;i<=16;++i)
      if(vertexEdgeDegree[i]!=3)throw std::runtime_error("NATIVE_VERTEX_DEGREE_CHANGED");
    // A single oriented closed shell is necessary evidence for the OCCT BRep
    // topology, not a formal all-point numerical set-equality certificate.
    BRepCheck_Analyzer analyzer(solid);
    const bool valid=analyzer.IsValid();
    if(!shell.Closed()||!valid)
      throw std::runtime_error("NATIVE_SHELL_NOT_CLOSED_OR_VALID");
    std::cout<<"{\"schema\":1,\"occt\":\""<<OCC_VERSION_COMPLETE
      <<"\",\"root_shape_type\":"<<static_cast<int>(root.ShapeType())
      <<",\"solid_count\":1,\"direct_shell_count\":"<<directShells
      <<",\"shell_count\":1,\"direct_shell_face_count\":10"
      <<",\"all_root_faces_identical_to_shell_faces\":true"
      <<",\"shell_closed\":true,\"brepcheck_valid\":true"
      <<",\"wire_count\":12,\"edge_count\":24,\"vertex_count\":16"
      <<",\"native_face_hierarchy\":[";
    for(int fi=1;fi<=10;++fi) {
      if(fi>1)std::cout<<',';
      std::cout<<"{\"face\":"<<(fi-1)<<",\"orientation\":\""
               <<ori(faces(fi).Orientation())<<"\",\"direct_wires\":[";
      for(size_t i=0;i<faceWires[fi].size();++i) {
        if(i)std::cout<<',';
        std::cout<<(faceWires[fi][i]-1);
      }
      std::cout<<"]}";
    }
    std::cout<<"],\"wires\":[";
    for(int wi=1;wi<=12;++wi) {
      if(wi>1)std::cout<<',';
      std::cout<<"{\"wire\":"<<(wi-1)<<",\"edge_ordinals\":[";
      for(size_t i=0;i<wireEdges[wi].size();++i) {
        if(i)std::cout<<',';
        std::cout<<(wireEdges[wi][i]-1);
      }
      std::cout<<"],\"orientations\":[";
      for(size_t i=0;i<wireOrientations[wi].size();++i) {
        if(i)std::cout<<',';
        std::cout<<'"'<<wireOrientations[wi][i]<<'"';
      }
      std::cout<<"]}";
    }
    std::cout<<"],\"edges\":[";
    for(int ei=1;ei<=24;++ei) {
      if(ei>1)std::cout<<',';
      std::cout<<"{\"edge\":"<<(ei-1)<<",\"face_pair\":["
               <<edgeUses[ei][0].face-1<<','<<edgeUses[ei][1].face-1
               <<"],\"vertex_pair\":["
               <<edgeVertex[ei][0]-1<<','<<edgeVertex[ei][1]-1<<"]}";
    }
    std::cout<<"],\"vertices\":[";
    for(int vi=1;vi<=16;++vi) {
      if(vi>1)std::cout<<',';
      const gp_Pnt p=BRep_Tool::Pnt(TopoDS::Vertex(verts(vi)));
      if(!std::isfinite(p.X())||!std::isfinite(p.Y())||!std::isfinite(p.Z()))
        throw std::runtime_error("NONFINITE_NATIVE_VERTEX");
      std::cout<<"{\"vertex\":"<<(vi-1)<<",\"point_mm\":["
               <<p.X()<<','<<p.Y()<<','<<p.Z()
               <<"],\"edge_degree\":"<<vertexEdgeDegree[vi]<<"}";
    }
    std::cout<<"],\"native_shell_membership_exhaustive\":\"PASS\""
             ",\"native_solid_material_set_equality\":\"UNKNOWN\""
             ",\"native_full_q_void_inclusion\":\"UNKNOWN\"}\n";
    return 0;
  } catch(const Standard_Failure& e) {
    std::cerr<<e.GetMessageString()<<'\n';return 3;
  } catch(const std::exception& e) {
    std::cerr<<e.what()<<'\n';return 3;
  }
}
