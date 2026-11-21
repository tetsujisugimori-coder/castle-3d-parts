# Stage 3-D-5D：実Guide Solidの境界Face過不足ゼロの限定審査

## 確認対象
固定`GATE_BoltGuide_Left.Shape.brp`（SHA256 `043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261`）、PR #46、OCCT 7.8.1、既存Qのみ。新しいCAD・新しい姿勢・追加UV点は作成しない。

「TopoDS_Solidを構成するFaceの全部を抽出できたか」と「それらが有限実誤差込みで実材料集合の境界を表すか」は区別する。前者はOCCTの**実親子構造**を列挙して検査できる。後者はトリムと面集合の数値意味論を含むため、今回の列挙だけで無条件PASSにしない。

## OCCTネイティブによる親子構造の網羅確認
`guide_solid_hierarchy.cpp`が元BRepを直接読み込み、ルートShapeから取得した全Solid・Shell・Face・Wire・Edge・Vertexを`TopExp::MapShapes`で列挙する。その上で、`TopoDS_Iterator`を用いて、**Solidの直接子ShellとShellの直接子Faceを別経路で走査**し、もとの10 Faceと`IsSame`の意味で一対一対応するか、余分な子・脱落・二重登録がないか判定する。Face直下Wire、Wire直下Edgeも独立に列挙する。

固定結果としてSolid1、Shell1、Face10（穴付き2）、Wire12、Edge24、Vertex16、Edge使用48、各Edgeは異なるFace2枚に使用、各Vertex次数3、全頂点接続、`BRepCheck_Analyzer.IsValid`、`Shell.Closed`を要求する。Solidが隠しFaceや異なるShellを持つならFAILにする。Face/Wireの方向も原票と照合する。

`verify_solid_hierarchy.py`は同じ出力の24 Edgeを、以前独立に保存した`trim-correspondence.json`の24 Edgeに**隣接Faceのペアと両端3D座標**で一対一対応させる。各FaceのWireと4 Edgeの構成、48個の元の保存pcurve使用、Edgeの両使用の向きが反対であること、16個のVertex座標・次数を照合する。全24 EdgeでFaceペアがそれぞれ固有であることも確認する。何らかの二重Edge、未接続Edge、Face欠落、偽の数値、非対応の頂点、余分な子があればFAIL。

## 証明範囲
- **Solidに格納されたBRepトポロジーのFace網羅性**：上記が合格すれば、Solid→1 Shell→10 Faceの実親子構造が過不足なく確認でき、各Faceの保存済みWire・Edgeとの一対一対応を示せる。これは直接ネイティブ観測と保存原票の独立照合である。
- **閉2次元多様体との構造整合**：Edgeが2面に共有され、16頂点が次数3で連結。穴付き端面2枚を円環（Euler寄与0）と数えると`V−E+(8×1+2×0)=16−24+8=0`。貫通穴を持つ一つの閉殻と整合する。ただし単なるEuler数0は、交差・非多様体の不存在を単独では証明しない。
- **幾何との結合**：保存48使用の各pcurveと直線・Plane、実ネイティブ10面の軸・Location、モデルQの最小距離1 mm、Plane直接点評価の有限誤差上界は旧工程の検査結果をそのまま使用する。今回の実Solid親子網羅と合わせ、**BRepが保持している境界Faceの全件**がQから離れているという証拠を強める。
- **残る条件**：OCCTの`TopoDS_Solid`という位相表現の境界と、数学的な全点材料集合の境界の一致（trimmed Faceの全点意味論、有限公差による同一性、全点の内部外部判定）は今回の検査だけでは形式的証明にならない。従って`native_material_boundary_real_set_equality=UNKNOWN`、`native_full_q_void_inclusion=UNKNOWN`、代表実区間NOT_TESTEDを維持。数値的`BRepExtrema`の報告値で代用もしない。

## 実行・保存
既存PR #46の専用CIで、これまでの`through-q`・`native-plane-bound`工程の後に1ステップだけネイティブ走査とPython証明票`solid-boundary-census.json`を生成する。独立した合成故障対照は既存のunit test discoverへ追加する。保存原票は同じ既存のartifact管理・manifest・SHAだけを使う。main変更、PR新設、原CAD再保存、無関係な検査の義務化、マージは行わない。
