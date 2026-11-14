"""Same-BBox negative controls for the actual mesh acceptance validator."""
import copy
import importlib.util
from pathlib import Path
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mesh_integrity',root/'scripts/stage3c-mesh-integrity.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
V=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1],[.5,.5,1]]
F=[[0,2,1],[0,3,2],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7],[4,5,8],[5,6,8],[6,7,8],[7,4,8]]
def box(vertices):return [min(v[i] for v in vertices) for i in range(3)]+[max(v[i] for v in vertices) for i in range(3)]

class MeshIntegrity(unittest.TestCase):
    def test_same_bbox_internal_vertex_corruption_is_rejected(self):
        bad=copy.deepcopy(V);bad[8][2]=.9
        self.assertEqual(box(V),box(bad))
        with self.assertRaises(AssertionError):module.compare_mesh(V,F,bad,F)

    def test_same_bbox_missing_and_reversed_faces_rejected(self):
        self.assertEqual(box(V),box(V))
        for bad in [F[:-1],[face[::-1] if i==0 else face for i,face in enumerate(F)],F+[F[0]]]:
            with self.assertRaises(AssertionError):module.compare_mesh(V,F,V,bad)

    def test_vertex_splitting_reordering_and_triangle_order_are_allowed(self):
        # glTF may split a shared vertex for normals, then reorder every vertex.
        actual=[];faces=[]
        for face in reversed(F):
            indices=[]
            for index in face:
                indices.append(len(actual));actual.append(V[index][:])
            faces.append(indices[1:]+indices[:1])
        result=module.compare_mesh(V,F,actual,faces)
        self.assertEqual(result['triangles'],len(F))
        self.assertEqual(result['unique_vertices'],len(V))

    def test_nonfinite_bad_indices_and_missing_source_vertices_rejected(self):
        for vertices,faces in [(V,[[0,1,99]]),([[float('nan'),0,0]]+V[1:],F),(V,[[True,1,2]])]:
            with self.assertRaises(AssertionError):module.compare_mesh(V,F,vertices,faces)
        with self.assertRaises(AssertionError):module.compare_mesh(V,F,V[:-1],F)

if __name__=='__main__':unittest.main()
