# Stage 3-D-5D：OCCT 7.8.1のFaceトリム意味論と実Guide材料境界の全点対応

## 検証する2つの命題
**命題A（数学的な全点命題）**：固定BRepの10個のネイティブ`Geom_Plane`、保存pcurve/向き付きWireから構成する**理想的なトリム済みFace集合**の和集合が、既存D2の4閉材料箱`M`の数学的境界 `∂M` と、全実数点で一致する。

**命題B（OCCT数値実装を含む全点命題）**：実際の`BRepClass_FaceClassifier`、`BRepClass3d_SolidClassifier`などが、任意の浮動小数表現可能点・公差近傍を含めて命題Aと同値の分類結果を返し、`TopoDS_Solid`の実材料集合に対する点ごとの保証となる。

Aを証明できてもBが自動的に成立するわけではない。今回Aを実証する条件を具体化し、Bについては証明できなければ**UNKNOWN**を維持する。

## OCCTの意味論と固定実体の結合
[OCCT 7.8.1 BRep_TFace.hxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_TFace.hxx#L32-L49)ではFaceはSurfaceとLocation、公差、`NaturalRestriction`を保持し、`NaturalRestriction=true`時はパラメータ領域の自然な境界を用いる。固定10面は元BRepから`BRep_Tool::Surface`を呼んで得たPlane・Locationを旧検証で実測済み。新規`guide_face_semantics.cpp`が全Faceの`NaturalRestriction`、Wire個数・閉鎖性・向き、実Solid/ShellのOrientationを同じ元BRepから直接記録する。

[OCCT 7.8.1 BRepClass_FaceExplorer.cxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRepClass/BRepClass_FaceExplorer.cxx#L39-L52)は分類時FaceのOrientationをFORWARDに正規化して扱い、[同L290–345](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRepClass/BRepClass_FaceExplorer.cxx#L290-L345)はWireとEdgeを走査する。[TopClass_FaceClassifier.gxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/TopClass/TopClass_FaceClassifier.gxx#L55-L151)はWireを走り、Edgeへの交差と向きを使ってIN/OUT/ONを判定する。これは正規な向き付きWireでトリムされたFaceという**抽象BRepの意味を示す実装上の根拠**である。ただし交差計算そのものの有限精度での全点厳密性は保証しない。

前工程で同じ元Guide BRepに対し次を確認済み：Solid→唯一のShell→ちょうど10 Face、Wire12、Edge24、48向き付き使用、全Edge2 Face共有、16頂点、保存pcurveと3D直線の全パラメータ域アフィン等式、ネイティブ10個のworld Planeとの係数同値、トリム済み外輪・内輪の矩形性、材料側を向く法線、Shell閉鎖性とBRepCheck有効性。新規証明はこれらの原証拠を同一固定SHAで結び付ける。

## 完全に独立なD2閉材料集合から境界を導出
`M` は、D2契約の元の4個の**閉**材料直方体の和集合である。その形状は次式に一致する（mm）。

`M=[-200,-180]×( ([-130,0]×[990,1050]) \ ((-116,-94)×(999,1041)) )`

内輪境界は材料に含まれる。Mは有界・正則閉集合（内部の閉包がM）。

したがって`∂M`は、
- X=−200と−180の**穴付き端面2枚**（各端面を4閉矩形帯に分割）、
- Y=−130,0およびZ=990,1050の**外側4面**、
- Y=−116,−94およびZ=999,1041の**穴内壁4面**、

という**合計10枚の向き付き面、分割後16枚の閉矩形片**の和集合になる。この導出は`BRepExtrema`にもOCCT数値分類器にも依存しない。

## 何が「有限サンプルではない全点証明」か
`occt_semantic_bridge.py` は、一方でネイティブのPlane・保存Wire・pcurve全パラメータから得た各トリム済みFaceを16枚の閉矩形片に分割し、もう一方で上記のD2閉材料集合から独立に16枚の理想境界片を生成する。

両者の端点座標で `R³` を**座標端点の単一点・隣接端点間の開区間・左右の無限開区間**へ分割する。今回の固定入力ではX方向5原子、Y方向9原子、Z方向9原子、計**405原子セル**である。任意の閉軸平行矩形への所属は、各原子セルの**全点で一定**だから、セル代表値に対する所属・法線集合の完全一致は、**R³の全点に対する集合と向きの一致の厳密な証明**である。単に「405点サンプリングしたので安全」と主張しているわけではない。内輪境界・面端部・稜線も原子セルの単一点として漏れなく扱う。

これにより命題A、すなわち`∂M = ⋃(10 native stored, ideal trimmed Faces)`が理想BRepの集合論では成立する。Face0/9の穴内部を誤って面に含める、Faceを1枚落とす、平面を移動する、法線を逆転する、D2材料箱を変更する場合は不一致として拒否する。

## 実Solidとの橋渡し、なお残る前提
OCCTの抽象的なBRep意味論として「境界が正しく向き付けられた閉じたShellで表され、Solidがその有界側の正則閉集合を表す」「各Faceの実体はPlaneを保存Wireで正しく制限した領域である」を採用するなら、固定ネイティブSolidの意味する**理想的な材料集合そのものがMに一致する**という条件付き結論を得られる。QはMと厳密に非交差なので、理想的なQ全点空洞は成立する。

**しかし**この意味論は、実装の`BRepClass3d_SolidClassifier`が実数または有限精度点すべてに同じ判断を返すという数値証明ではない。[OCCT BRepClass3d_SClassifier.cxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRepClass3d/BRepClass3d_SClassifier.cxx#L191-L217)は公差範囲のEdge/VertexでONを返す例がある。したがって`native_numeric_faceclassifier_all_point_equivalence=UNKNOWN`、`native_numeric_solidclassifier_all_point_equivalence=UNKNOWN`、`native_material_real_set_boundary_equivalence=UNKNOWN`、`native_full_q_void_inclusion=UNKNOWN`を堅持する。有限実数演算全体の上界、128区間、閂代表区間は本工程の対象外。

## 実施範囲と証拠
PR #46の既存ブランチ内で、新規C++による全10面のNative Face意味論フラグ記録、既存48使用・Solid境界証明票と結合する有理数証明器、合成故障対照、既存専用CIの1ステップだけを追加する。元FCStd・D2契約・元BRep・旧ZIPは不変更。新しい数値点サンプリング、不要な再探索、別PR作成、main更新、マージは行わない。
