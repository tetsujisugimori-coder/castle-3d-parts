# Stage 3-D-5D: Guide実BRep公差とQ非交差条件の限定監査

## 固定対象と問い
既存 `GATE_BoltGuide_Left.Shape.brp`、OCCT 7.8.1、10 Geom_Plane Face、12 Wire、24 Edge、16 Vertex、48保存pcurve使用、D2の閉Q `[-201,-179]×[-115,-95]×[1000,1040] mm`。原CAD・D2・保存pcurve原票は変更しない。研究の狙いは**公差観測・誤差上界・理想BRepの集合意味論を混同せず**、固定Qの非交差についてどこまで言えるか整理すること。

## 実測するもの
`guide_tolerance_audit.cpp` が、実BRepの全Face/Edge/Vertexへ `BRep_Tool::Tolerance` を適用し、10/24/16個を記録する。同じ実BRepを走査して48のFace/Wire/Edge使用に対し、stored pcurveの存在、`SameParameter`、`SameRange`、3D/2Dパラメータ範囲一致、Plane/Line型、非退化を記録する。保存元からの48使用と照合する`verify_tolerance_audit.py` は旧`stored_pcurve`と`trim-correspondence`で証明済みの**保存ハンドル由来・全パラメータ域でのアフィン係数同値・世界座標Location一致**を前提として要求し、同一性が崩れたら失敗にする。故障対照では、false flag/非有限公差/保存使用の欠損/不正なPASS昇格を拒否する。

## 何を測定から推論しないか
OCCTのEdge toleranceは3D曲線とFace上の表現が許容される局所的基準である。`SameParameter`と`SameRange`は重要な整合条件だが、検査フラグを浮動小数演算の**総誤差上界**へ昇格しない。Face/Edge/Vertexの最大公差が1 mmより小さくても`delta_total<1 mm`の証明ではない。全ネイティブ形状の丸め・交差器・最適化・トリム分類器・公差伝播には別途明示的な上界が必要。

## 証明済みの厳密モデルと必要条件
D2の4閉材料箱の和を`M`とする。旧工程で、実BRep由来の10トリム済みFace（穴あり端面2面を含む）の理想幾何集合と`∂M`は405原子空間分割で全点・法線集合一致を検査した。Qと`∂M`の理想距離は厳密に1 mm。独立のcross-section計算でQは全ての4閉箱と非交差し、中心から`(-∞,-105,1020)`へ伸びるx負方向の経路もMと非交差する。Qは凸で連結だから、**抽象BRepが正則閉・向き付きShellの有界材料側を表す意味論の下**でQの全点は非有界補集合（理想空洞）に属する。ここでは実装版`SolidClassifier`の全点IN/OUTを仮定しない。

真のnative材料境界が理想`∂M`からHausdorff方向で最大`δ`だけずれるという**別途証明済みの上界**が存在する場合、距離の1-Lipschitz性から`dist(Q,∂S_native)≥1−δ>0`が`δ<1mm`で成立する。ただし境界非交差だけでは閉領域の内外は定まらず、外部に通る経路・向き付き材料側の結合も保証しなければならない。前工程のPlane直接`D0`評価に対する上界（約3.744×10⁻¹² mm）は、その**限定評価操作の点にのみ**適用可能。すべてのトリム分類操作・曲線評価・位相判断を包絡した`δ_total`ではない。

## 未解決の誤差経路（今回必要な範囲）
1. pcurveパラメータ計算の丸め、CurveOnSurfaceと3D Curve点評価の値に対する全パラメータ域の有限精度包絡
2. Edge/Wire近傍の数値トリム分類・交点選択・Vertex tolerance伝播
3. Face/Edge/VertexのLocation合成による点評価と分類器内の座標変換経路
4. これらが記録済みの厳密トリム面から作る**材料境界全体**を確実に包絡することの保証

既存の厳密アフィン幾何証明とPlane直接評価の限定証明は再利用する。今回の監査が合格しても `native_full_q_void_inclusion=UNKNOWN`、`native_representative_interval=NOT_TESTED`、PR Draft・マージHOLDを維持する。

## 参照
- [OCCT BRep_Tool](https://occt3d.com/dev/doc/refman/html/class_b_rep___tool.html)
- [OCCT BRepCheck_Analyzer](https://occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html)
- [前工程の全点意味論証明](OCCT-TRIM-SOLID-SEMANTICS.md)
- [OCCT Plane直接評価上界](NATIVE-PLANE-ROUNDOFF-BOUND.md)
