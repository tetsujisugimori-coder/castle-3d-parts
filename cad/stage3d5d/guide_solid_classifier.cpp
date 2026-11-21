// Fixed Guide BRep: bounded OCCT point-classifier observations, never a set theorem.
#include <BRep_Builder.hxx>
#include <BRepTools.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepClass3d_SolidClassifier.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS.hxx>
#include <TopAbs_State.hxx>
#include <Precision.hxx>
#include <Standard_Version.hxx>
#include <gp_Pnt.hxx>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

static const char* status(TopAbs_State s) {
  switch(s) {
    case TopAbs_IN: return "IN";
    case TopAbs_OUT: return "OUT";
    case TopAbs_ON: return "ON";
    default: return "UNKNOWN";
  }
}
static bool valid_label(const std::string& label) {
  if (label.empty() || label.size() > 60) return false;
  for (char c : label)
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '_' || c == '-')) return false;
  return true;
}
int main(int argc, char** argv) {
  std::cout.imbue(std::locale::classic());
  std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
  try {
    if (argc != 3) throw std::runtime_error("USAGE: guide_solid_classifier guide.Shape.brp samples.tsv");
    TopoDS_Shape shape;
    BRep_Builder builder;
    if (!BRepTools::Read(shape, argv[1], builder) || shape.IsNull())
      throw std::runtime_error("BREP_READ_FAILED");
    TopTools_IndexedMapOfShape solids;
    TopExp::MapShapes(shape, TopAbs_SOLID, solids);
    if (solids.Extent() != 1) throw std::runtime_error("EXPECTED_ONE_SOLID");
    const auto solid = TopoDS::Solid(solids(1));
    BRepCheck_Analyzer analyzer(solid);
    const bool valid = analyzer.IsValid();
    BRepClass3d_SolidClassifier classifier(solid);
    std::ifstream source(argv[2]);
    if (!source) throw std::runtime_error("POINT_REQUEST_UNAVAILABLE");
    const double tol = Precision::Confusion();
    if (!(tol > 0 && std::isfinite(tol))) throw std::runtime_error("INVALID_CLASSIFIER_TOL");
    std::cout << "{\"schema\":1,\"occt\":\"" << OCC_VERSION_COMPLETE
              << "\",\"solid_count\":1,\"valid_observed\":" << (valid ? "true" : "false")
              << ",\"classifier_tolerance_mm\":" << tol << ",\"samples\":[";
    std::string label;
    double x,y,z;
    unsigned count = 0;
    while (source >> label >> x >> y >> z) {
      if (!valid_label(label) || !std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z)
          || ++count > 32) throw std::runtime_error("INVALID_POINT_REQUEST");
      classifier.Perform(gp_Pnt(x,y,z), tol);
      if (count > 1) std::cout << ',';
      std::cout << "{\"id\":\"" << label << "\",\"point_mm\":[" << x << ',' << y << ',' << z
                << "],\"state\":\"" << status(classifier.State()) << "\"}";
    }
    if (!source.eof() || count < 6) throw std::runtime_error("POINT_REQUEST_TRUNCATED");
    std::cout << "],\"sample_count\":" << count
              << ",\"native_material_outer\":\"UNKNOWN\",\"native_void_inner\":\"UNKNOWN\"}\n";
    return valid ? 0 : 2;
  } catch (const Standard_Failure& ex) {
    std::cerr << ex.GetMessageString() << '\n';
    return 3;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << '\n';
    return 3;
  }
}
